"""Blueprint clustering.

WARNING: This documentation may be outdated.

Blueprint takes as input OCRed words and their bounding boxes (sometimes called
wordpolys). To enable extraction of multi-word (full names, cities, multi-word
labels) or multi-line (addresses) entities, Blueprint generates clusters.

A *cluster* is an entity which is made up of smaller entities. We have two kinds
of clusters: *phrases* and *multiline clusters*.

A *phrase* is a sequence of words such that the words are roughly on the same
baseline, separated by widths which are roughly equal to single typographic
spaces. In other words, a phrase is a sequence of contiguous words on the same
line that are (usually) part of the same semantic thread.

A *multiline cluster* is (for now) a sequence of words or phrases that are
roughly left-aligned, have roughly similar line heights, etc.

Phrases and multiline clusters can overlap. For example, in this sentence, both
"For example," and "example, in" are phrases. Multiline clusters can also
overlap. If we OCRed this paragraph, the first two lines would be a multiline
cluster, and the second and third lines together would be a multiline cluster,
and the first three lines would also be a multiline cluster.

The reason we allow overlap is that the things Blueprint will return as
extraction "values" are entities. So, if something isn't in captured as an
entity by Blueprint, it won't be a candidate for extraction. It isn't possible
to know where to draw the cluster boundary lines by looking only at the
low-level OCR results. For example, the following are dollar-and-cents amounts
from a densely-packed table where OCR didn't capture punctuation:

    ... 12 34 56 78 90 ...

Without looking at the table headings, we can't tell which of these is going on
(semantically):

    ... $12.34 $56.78 $90...
    ...12 $34.56 $78.90 ...

The solution is to include both "12 34" and "34 56", etc., as entities, and let
the search algorithm (as opposed to the clustering algorithm) pick the right
one.

(If the thing you want to extract isn't captured as an entity by Blueprint, you
could still in principle extract a bigger entity and clean it up in
post-processing, or extract multiple entities by hand and merge them manually.
Hopefully this isn't necessary most of the time.)

We detect phrases in the clustering step of Blueprint by looking at things like
between-word spacing, line height consistency, and so on. Ideally we would use
font information, as well. We compute a score based on these metrics, and if a
collection of words exceeds a certain threshold then it is considered a phrase,
and an entity is created having those words as a phrase.

History:

We used to get maximal phrases from the Microsoft Read API. It returns them to
us (labeled as "lines") in addition to the underlying words. It seems that the
MSRAPI's clustering algorithm achieves pretty good results. Speculating, my
guess is that it uses font information, text height, vertical alignment,
interword spacing consistency, etc. The MSRAPI does not return overlapping
phrases.
"""

import functools
import heapq
import operator
import statistics

from dataclasses import replace
from itertools import chain, filterfalse
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, Sequence, Tuple

from ..document import DocRegion, Document, EZDocRegion
from ..entity import Entity, Page, Text, Word
from ..functional import all_equal
from ..geometry import BBox, Interval
from ..ocr import InputWord


def sort_word_cluster(cluster: List[Text],
                      valid_eps: float = 0.1) -> Iterable[Iterable[Text]]:
  """Sort word cluster as list of entities into top-down, left-to-right lines.

    The idea is to iteratively find the top-most bounding box in a list of
    bboxes. Define a valid region (in y) around that bbox, and iterate over
    the list of bboxes in order of increasing ix.a. The 'valid' bounding boxes
    form a left-to-right line of text. Repeat, with bboxes belonging to that
    line removed.

    Args:
      cluster: list of entities, representing a cluster.
      valid_eps: controls the tolerance above and below a bbox for same-line
                 validity (unit relative to bbox height)
    Returns:
      Generator yielding each line as a generator. Each line in turns yields
        an entity.
      Lines are yielded top-to-bottom. Entities in a line are yielded
        left-to-right.
    """

  bboxes = [e.bbox for e in cluster]
  left_to_right = sorted(enumerate(bboxes), key=lambda ib: ib[1].ix.a)
  left_to_right_ixs = [i for i, _ in left_to_right]

  def topmost(box_ids: List[int]) -> int:
    return min(box_ids, key=lambda i: bboxes[i].iy.a)

  def valid_region(box_id: int) -> Interval:
    bbox = bboxes[box_id]
    C = valid_eps * bbox.height
    return Interval(bbox.iy.a - C, bbox.iy.b + C)

  while left_to_right_ixs:
    tl = topmost(left_to_right_ixs)
    region = valid_region(tl)
    validity_predicate = lambda i: bboxes[i].center.y in region
    cur_line = filter(validity_predicate, left_to_right_ixs)
    left_to_right_ixs = list(
        filterfalse(validity_predicate, left_to_right_ixs))

    yield (cluster[i] for i in cur_line)


def _suffixes(xs: Tuple[Any, ...]) -> Generator[Tuple, None, None]:
  for i in range(len(xs)):
    yield xs[i:]


def _build_clusters(
    Es: Iterable[Text],
    score_computer: Callable[[Text], float],
    bounder: Callable[[Text], DocRegion],
    page: Page,
    document: Document,
    max_tup_length_in_cluster: int,
  ) -> Tuple[Text, ...]:
  """Build clusters from the input entities.

  The algorithm builds horizontal or vertical clusters from the input entities.
  To build phrases, we pass in a list of words. To build vertical clusters, we
  pass in a list of (maximal) phrases.

  The algorithm keeps track of the clusters found so far in a space partition
  data structure allowing fast spatial queries. To incorporate the next entity
  in the input list, we attempt to append it to every cluster found so far, and
  keep those newly-formed clusters that are valid, according to the score or
  rules that define cluster validity.

  Args:
    Es: Entities to cluster. These should be sorted left-to-right by x_min if
      you are building horizontal phrases, and top-down by y_min if you are
      building vertical clusters.
    score_computer: Returns the quality of a cluster candidate. FIXME: Also
      mutates the candidate's metadata, recording the score and computations
      related to clustering.
    bounder: Given an entity, returns a document region D such that if C is a
      cluster and build_text(C, B) is also a valid cluster, then C meets D.
    page: The page where these clusters live.
    max_tup_length_in_cluster: Upper-bound the size of the generated clusters.
  """

  def doc_region(tup: Tuple[Text, ...]) -> DocRegion:
    bbox = BBox.spanning(
      chain.from_iterable(
        E.bbox.corners() for E in tup))
    assert bbox
    return DocRegion(document, bbox)

  ez_doc_region: EZDocRegion[Tuple[Text, ...]] = EZDocRegion(doc_region)

  for E in Es:

    @functools.lru_cache(maxsize=None)
    def can_append_to(tup: Tuple[Text]) -> bool:
      if len(tup) + 1 > max_tup_length_in_cluster:
        return False
      return score_computer(build_text(tup + (E,), None, None)) > 0

    new_tups: List[Tuple[Text, ...]] = [(E,)]
    for tup in ez_doc_region.ts_intersecting(bounder(E)):
      if all(map(can_append_to, _suffixes(tup))):
        new_tups.append(tup + (E,))

    for tup in new_tups:
      ez_doc_region.insert(tup)

  # FIXME: This is janky. Just maximality computation/marking.
  tups = tuple(sorted(ez_doc_region.ts(), key=len))
  result: Dict[Tuple[Entity, ...], Entity] = {}
  for tup in tups:
    cluster = build_text(tup, 1.0, None)
    score = score_computer(cluster)
    cluster = replace(cluster, ocr_score=score)
    result[tup] = cluster
    if len(tup) > 1:
      if tup[1:] in result:
        result[tup[1:]] = replace(result[tup[1:]], maximality_score=0.0)

      assert tup[:-1] in result
      result[tup[:-1]] = replace(result[tup[:-1]], maximality_score=0.0)

  return tuple(text for text in result.values() if isinstance(text, Text))


def build_multiline_clusters(
    maximal_phrases: Iterable[Text],
    page: Page,
    document: Document,
    max_num_lines: int=6) -> Tuple[Text, ...]:
  # FIXME: We should be able to have multiline clusters across pages.
  def multiline_cluster_bounder(word: Text) -> DocRegion:
    # FIXME: This could be more precise. Also I'm not 100% sure this is right.
    y = word.bbox.iy.a
    return DocRegion(
      document,
      BBox(word.bbox.ix, Interval(y - 2 * entity_height(word), y)))
  multiline_clusters = _build_clusters(
      sorted(maximal_phrases, key=lambda E: E.bbox.iy.a),
      compute_multiline_cluster_score,
      multiline_cluster_bounder, page, document,
      max_num_lines)
  return multiline_clusters


def build_words_and_phrases(
    words: Iterable[Text],
    page: Page,
    document: Document,
    max_num_words_in_phrase: int=6) -> Tuple[Text, ...]:
  def phrase_bounder(word: Text) -> DocRegion:
    # FIXME: This could be more precise. Also I'm not 100% sure this is right.
    x = word.bbox.ix.a
    return DocRegion(
      document,
      BBox(Interval(x - 6 * entity_height(word), x), word.bbox.iy))
  return _build_clusters(
      sorted(words, key=lambda E: E.bbox.ix.a),
      compute_ocr_score, phrase_bounder, page, document,
      max_num_words_in_phrase)


def _score_deviation(
    deviation: float, tolerance: float, taper_dist: float) -> float:
  assert deviation >= 0
  return max(0.0, 1.0 - max(0.0, deviation - tolerance) / taper_dist)


def _score_consistency(
    vals: Iterable[float], tolerance: float, taper_dist: float) -> float:
  return _score_deviation(max(vals) - min(vals), tolerance, taper_dist)


def compute_ocr_score(E: Text) -> float:
  """Compute the phrase score.

  FIXME: These methods effectively mutate entities, which we don't do anywhere
  except in the clustering code. They add the phrase/cluster scores as metadata
  fields. We could use memoization here, but it would incur a permanent memory
  penalty, which is annoying, and there is no natural size at which to cap the
  cache size.

  FIXME: For an entity to be considered a valid phrase, in addition to the
  computed scores below being positive, we require that every contiguous
  subsequence of its words is also a valid phrase. This check is not performed
  in this file, but at the clustering algorithm level. The same thing is true
  for multiline clusters.
  """
  words: Tuple[Entity, ...] = tuple(E.words)
  if len(words) == 1:
    return 1.0

  assert len(words) >= 2

  baseline = entity_baseline(words)
  def average_char_height(words: Sequence[Entity]) -> float:
    # FIXME: This does not work correctly for text at an angle.
    # FIXME: This isn't really right at all.
    assert(all(isinstance(W, Word) for W in words))

    return sum(len(word.entity_text or '') * entity_height(word) for word in words) \
            / sum(len(word.entity_text or '') for word in words)
  ave_char_height = average_char_height(words)
  word_baselines = [entity_baseline([word]) for word in words]
  word_heights = [entity_height(word) for word in words]
  def left_right_horizontal_distance(E1: Entity, E2: Entity) -> float:
    return E2.bbox.ix.a - E1.bbox.ix.b
  interword_distances = [
      left_right_horizontal_distance(words[i], words[i + 1])
      for i in range(len(words) - 1)
  ]
  baseline_deviations = [
      abs(word_baseline - baseline) for word_baseline in word_baselines
  ]

  # We use this as a unit.
  mu = ave_char_height

  min_interword_distance = 0.0 * mu
  interword_deviations_from_min = [
      max(0, min_interword_distance - interword_distance)
      for interword_distance in interword_distances
  ]

  max_interword_distance = 0.8 * mu
  interword_deviations_from_max = [
      max(0, interword_distance - max_interword_distance)
      for interword_distance in interword_distances
  ]

  word_height_consistency_score = _score_consistency(
      word_heights, 0.3 * mu, 0.5 * mu)
  baseline_deviation_score = _score_deviation(
      max(baseline_deviations), 0.1 * mu, 0.3 * mu)
  interword_distance_consistency_score = _score_consistency(
      interword_distances, 0.3 * mu, 0.8 * mu)
  interword_deviation_from_min_score = _score_deviation(
      max(interword_deviations_from_min), 0.0 * mu, 1.0 * mu)
  interword_deviation_from_max_score = _score_deviation(
      max(interword_deviations_from_max), 0.0 * mu, 1.0 * mu)

  computed_score = word_height_consistency_score * baseline_deviation_score * \
          interword_distance_consistency_score * interword_deviation_from_max_score * \
          interword_deviation_from_min_score

  score = computed_score if computed_score > 0.5 else 0

  return score


def compute_multiline_cluster_score(E: Text) -> float:
  # FIXME: This should be a trained ML model.
  # FIXME: This doesn't handle clusters on a slant.
  # FIXME: This doesn't handle right-aligned or center-alinged clusters.

  Es = E.words

  if len(Es) == 1:
    return 1.0

  assert len(Es) >= 2

  line_heights = [entity_height(E) for E in Es]
  baseline_separations = [
    baseline_separation(Es[i], Es[i + 1]) for i in range(len(Es) - 1)
  ]
  average_x = statistics.mean([E.bbox.ix.a for E in Es])
  # FIXME: x deviation should be compared to a best-fit line (if we don't just use an ML model).
  x_deviations = [abs(E.bbox.ix.a - average_x) for E in Es]
  def average_char_width(E: Word) -> float:
    # FIXME: This does not work correctly for text at an angle.
    assert isinstance(E, Word)
    return E.bbox.width / len(E.text)
  average_char_widths = [average_char_width(E) for E in Es]

  # We use this as a unit.
  mu = statistics.mean(line_heights)

  min_baseline_separation = 1.0 * mu
  baseline_separation_deviations_from_min: List[float] = [
      max(0, min_baseline_separation - baseline_separation)
      for baseline_separation in baseline_separations
  ]

  max_baseline_separation = 1.5 * mu
  baseline_separation_deviations_from_max = [
      max(0, baseline_separation - max_baseline_separation)
      for baseline_separation in baseline_separations
  ]

  line_height_consistency_score = _score_consistency(
      line_heights, 0.1 * mu, 0.1 * mu)
  baseline_separation_consistency_score = _score_consistency(
      baseline_separations, 0.3 * mu, 0.3 * mu)
  x_deviation_score = _score_deviation(max(x_deviations), 0.5 * mu, 0.5 * mu)
  average_char_width_consistency_score = _score_consistency(
      average_char_widths, 0.4 * mu, 0.5 * mu)
  baseline_separation_deviation_from_min_score = _score_deviation(
      max(baseline_separation_deviations_from_min), 0.0 * mu, 0.2 * mu)
  baseline_separation_deviation_from_max_score = _score_deviation(
      max(baseline_separation_deviations_from_max), 0.0 * mu, 0.5 * mu)

  computed_score = line_height_consistency_score * baseline_separation_consistency_score * \
          x_deviation_score * average_char_width_consistency_score * \
          baseline_separation_deviation_from_max_score * \
          baseline_separation_deviation_from_min_score

  score = computed_score if computed_score > 0.5 else 0

  return score


def entity_height(E: Entity) -> float:
  # FIXME: This does not work correctly for text at an angle.
  return E.bbox.height


def entity_baseline(words: Sequence[Entity]) -> float:
  # FIXME: This does not work correctly for text at an angle.

  word_baselines = [W.bbox.iy.b for W in words]
  if len(word_baselines) == 1:
    return word_baselines[0]

  lengths = [len(W.entity_text or '') for W in words]
  return sum(w_length * bl for (w_length, bl) in zip(lengths, word_baselines)) \
    / sum(lengths)


def baseline_separation(E1: Entity, E2: Entity) -> float:
  # FIXME: This does not work correctly for text at an angle.
  return abs(
    entity_baseline(
      tuple(E1.entity_words())) - entity_baseline(tuple(E2.entity_words())))


def build_text(
  Es: Tuple[Text, ...],
  maximality_score: Optional[float],
  ocr_score: Optional[float]) -> Text:
  """Construct a Entity of type Text."""
  return Text.from_words(
    tuple(chain.from_iterable(E.words for E in Es)),
    maximality_score, ocr_score)
