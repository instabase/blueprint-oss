"""Rules about text."""

import re

from bisect import bisect
from dataclasses import dataclass
from enum import auto, Flag
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..document import Document
from ..entity import Address, Cluster, Entity, Text
from ..rule import AtomScore, Degree1Predicate, DegreeError, Predicate, RuleScore
from ..string_algos import edit_distance as sa_edit_distance, substring_edit_distance as sa_substring_edit_distance, pattern_edit_distance as sa_pattern_edit_distance
from ..text_properties import length as tp_length, legal_chars as tp_legal_chars, min_char_proportions as tp_min_char_proportions, max_char_proportions as tp_max_char_proportions, min_char_counts as tp_min_char_counts, max_char_counts as tp_max_char_counts

from .logical import negate

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


class TextComparisonFlags(int, Flag): # type: ignore
  """
  For the type ignore: https://github.com/python/mypy/issues/9319
  """
  NONE = 0
  CASE_SENSITIVE = auto()
  NO_WHITESPACE = auto()
  ALPHABETICAL = auto()
  NUMERICAL = auto()
  ALPHANUMERICAL = ALPHABETICAL | NUMERICAL


def _text_comparison_massage(
    text_comparison_flags: TextComparisonFlags, s: str) -> str:
  if TextComparisonFlags.CASE_SENSITIVE not in text_comparison_flags:
    s = s.upper()
  if TextComparisonFlags.NO_WHITESPACE in text_comparison_flags:
    s = re.sub('\s', '', s)
  if TextComparisonFlags.ALPHANUMERICAL in text_comparison_flags:
    s = re.sub('[^a-zA-Z0-9]', '', s)
  elif TextComparisonFlags.ALPHABETICAL in text_comparison_flags:
    s = re.sub('[^a-zA-Z]', '', s)
  elif TextComparisonFlags.NUMERICAL in text_comparison_flags:
    s = re.sub('[^0-9]', '', s)
  return s


def _taper_error(raw_error: int, tolerance: int, taper: int) -> float:
  assert raw_error >= 0
  assert tolerance >= 0
  assert taper >= 0
  error = max(0, raw_error - tolerance)
  if error == 0:
    return 1.0
  if taper == 0:
    return 0.0
  # abs to avoid -0.0 in output.
  return abs(1.0 - min(1.0, error / (taper + 1)))


def count_score(score_dict: Dict, count: int) -> float:

    if count in score_dict:
      return score_dict[count]

    counts = sorted(score_dict.keys())
    assert len(set(counts)) == len(counts)

    i = bisect(counts, count)

    if i == len(counts):
      return score_dict[counts[-1]]
    assert counts[i] > count

    if i == 0:
      return score_dict[counts[0]]
    assert counts[i - 1] < count

    t = (count - counts[i - 1]) / (counts[i] - counts[i - 1])
    return score_dict[counts[i-1]] + \
            (score_dict[counts[i]] - score_dict[counts[i-1]]) * t


@dataclass(frozen=True)
class LineCountIs(Degree1Predicate):
  """Says a field has one of the given line counts.

  This is useful for dealing with multiline text.

  Args:
    score_dict: A map from word-count to score. For word counts above the
      largest or below the smallest map key, we use the scores corresponding to
      the largest and smallest map keys, respectively. We linearly interpolate
      to compute scores for absent intermediate word counts.

  In the following example code, the resulting score, depending on the
  assignment for the field, will be:
    * 0 for assignments having 1 or fewer words, or 5 words,
    * 0.5 for assignments having 2 words,
    * 0.75 for assignments having 3 words (due to lerping),
    * 1 for assignments having 4 words, and
    * 0.3 for assignments having 6 or more words.

  Example code:
    word_count_is(score_dict={
      1: 0,
      2: 0.5,
      4: 1,
      5: 0,
      6: 0.3,
    })('shipping_address')
  """

  score_dict: Dict

  def __init__(
    self,
    score_dict: Dict,
    name: str = 'line_count_is',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'score_dict', score_dict)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]

    # TODO: Support more Entity types; support multiline Text Entities.
    line_count = len(E.lines) if isinstance(E, Cluster) \
        or isinstance(E, Address) else 1
    return AtomScore(count_score(self.score_dict, line_count))

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    if type(self) != type(other):
      return False
    return hash(self) == hash(other)


@dataclass(frozen=True)
class WordCountIs(Degree1Predicate):
  """Says a field has one of the given number of word counts.

  Similar to `line_count_is`. See the docs for that rule for an example.

  Args:
    score_dict: A map from word-count to score. For word counts above the
      largest or below the smallest map key, we use the scores corresponding to
      the largest and smallest map keys, respectively. We linearly interpolate
      to compute scores for absent intermediate word counts.
  """

  score_dict: Dict

  def __init__(
    self,
    score_dict: Dict,
    name: str = 'word_count_is',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'score_dict', score_dict)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    if not isinstance(E, Text):
      raise TypeError('WordCountIs only works with Text entities')
    return AtomScore(count_score(self.score_dict, len(tuple(E.words))))

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    if type(self) != type(other):
      return False
    return hash(self) == hash(other)


@dataclass(frozen=True)
class TextEquals(Degree1Predicate):
  """Says a field's text matches one of the given texts.

  The measured error is the edit distance between the texts: the minimum number
  of character additions, deletions, or substitutions required to make the texts
  equal.

  (The edit distance is also known as the Levenshtein distance.)

  Args:
    texts: Candidate texts to match. The best match will be used. If no texts
      are provided, the rule will score 1.
    text_comprison_flags: Flags to describe how to perform the comparison.
    tolerance: Will score 1 if the measured error is at most this amount.
    taper: The score tapers from 1 to 0 as the measured error minus the
      tolerance goes from 0 to taper+1 inclusive. Must be nonnegative.
  """

  texts: Tuple[str, ...]
  text_comparison_flags: TextComparisonFlags
  tolerance: int
  taper: int

  def __init__(
    self,
    texts: Tuple[str, ...],
    text_comparison_flags: TextComparisonFlags = TextComparisonFlags.NONE,
    tolerance: int = 1,
    taper: int = 1,
    name: str = 'text_equals',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'texts', texts)
    object.__setattr__(self, 'text_comparison_flags', text_comparison_flags)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]

    if not self.texts:
      return AtomScore(1)

    if not hasattr(E, 'text'):
      if '' in self.texts:
        return AtomScore(1)
      else:
        return AtomScore(0)

    if not isinstance(E.text, str): # type: ignore
      raise RuntimeError(
        'if your Entity has a text attribute, it should be a string')
    E_text: str = E.text # type: ignore
    E_text = _text_comparison_massage(self.text_comparison_flags, E_text)

    def match_score(text: str) -> float:
      if abs(len(text) - len(E_text)) > self.tolerance + self.taper:
        return 0
      error = sa_edit_distance(text, E_text)
      return _taper_error(error, self.tolerance, self.taper)

    best: Optional[float] = None
    for text in self.texts:
      text = _text_comparison_massage(self.text_comparison_flags, text)
      this_match_score = match_score(text)
      if best is None or best < this_match_score:
        best = this_match_score
      if best == 1:
        return AtomScore(best)

    assert best is not None
    return AtomScore(best)

  def __hash__(self) -> int:
    return id(self).__hash__()


def text_is_one_of(
    texts: Tuple[str, ...],
    text_comparison_flags: TextComparisonFlags = TextComparisonFlags.NONE,
    tolerance: int = 1,
    taper: int = 1) -> TextEquals:
  return TextEquals(texts, text_comparison_flags, tolerance, taper)


def text_equals(
    text: str,
    text_comparison_flags: TextComparisonFlags = TextComparisonFlags.NONE,
    tolerance: int = 1,
    taper: int = 1) -> TextEquals:
  return TextEquals((text,), text_comparison_flags, tolerance, taper)


@dataclass(frozen=True)
class TextHasSubstring(Degree1Predicate):
  """Says the given text is a substring of of a field's text.

  The measured error is the the minimum number of character additions,
  deletions, or substitutions required to make the given text a substring of the
  field's text.

  Args:
    text_comprison_flags: Flags to describe how to perform the comparison.
    tolerance: Will score 1 if the measured error is at most this amount.
    taper: The score tapers from 1 to 0 as the measured error minus the
      tolerance goes from 0 to taper+1 inclusive. Must be nonnegative.
  """

  text: str
  text_comparison_flags: TextComparisonFlags
  tolerance: int
  taper: int

  def __init__(
    self,
    text: str,
    text_comparison_flags: TextComparisonFlags,
    tolerance: int,
    taper: int,
    name: str = 'text_has_substring',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'text', text)
    object.__setattr__(self, 'text_comparison_flags', text_comparison_flags)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    if not isinstance(E, Text):
      return AtomScore(0)
    local_taper = self.taper
    if local_taper is None:
      local_taper = 0.5 * len(self.text)
    assert local_taper >= 0
    _text = _text_comparison_massage(self.text_comparison_flags, self.text)
    _E_text = _text_comparison_massage(self.text_comparison_flags, E.text)
    error = sa_substring_edit_distance(_E_text, _text)
    return AtomScore(_taper_error(error, self.tolerance, local_taper))


def text_has_substring(
    text: str,
    text_comparison_flags: TextComparisonFlags = TextComparisonFlags.NONE,
    tolerance: int = 1,
    taper: int = 1) -> TextHasSubstring:
  return TextHasSubstring(text, text_comparison_flags, tolerance, taper)


def text_does_not_contain_substring(
    text: str,
    text_comparison_flags: TextComparisonFlags = TextComparisonFlags.NONE,
    intolerance: int = 0,
    taper: int = 0) -> Predicate:
  """Says the given text is not a substring of of a field's text.

  The measured distance is the the minimum number of character additions,
  deletions, or substitutions required to make the given text a substring of the
  field's text.

  Args:
    text_comparison_flags: Flags to describe how to perform the comparison.
    intolerance: Will score 0 if the measured distance is at most this amount.
    taper: The score tapers from 0 to 1 as the measured distance minus the
      intolerance goes from 0 to taper+1 inclusive. Must be nonnegative.
  """

  return negate(
    text_has_substring(text, text_comparison_flags, intolerance, taper))


@dataclass(frozen=True)
class TextMatchesPattern(Degree1Predicate):
  """Says a field's text matches the pattern.

  Compares the field's text to the given pattern. Counts the number of errors:
  the smallest number of edits to the field's text required for the pattern to
  match perfectly.

  Useful for things like social security numbers.

  Characters in the pattern are treated as literals, unless they appear in as
  keys in the the stands_for dictionary, in which case they "stand for" any one
  of the values in stands_for[char].

  Warnings: If you override the default value of stands_for, you may want to
  include the default-specified behavior for '#' and 'A', and you'd have to do
  so explicitly.

  Args:
    pattern: A string to match the field's text against.
    stands_for: A dictinary from character to collection of characters (a
      string). When comparing the field's text to the given pattern, anytime a
      key in this dictionary appears in the pattern, any of the characters in
      the corresponding dictionary value will be considered a pattern match. See
      the example below.
    tolerance: Will score 1 if the measured error is at most this amount.
    taper: The score tapers from 1 to 0 as the measured error (minus the
      tolerance) goes from 0 to taper+1 inclusive. Defaults to 0.5 *
      max(len(E.text), len(pattern)).

  Example code:
    # Will score 1 for assignments having text "XXX-XX-1234", "XXX-xx-5555"
    text_matches_pattern("XXX-XX-DDDD",
        stands_for={"X": "Xx", "D": "0123456789"})
  """

  pattern: str
  stands_for: Dict
  tolerance: int
  taper: Optional[int]

  def __init__(
    self,
    pattern: str,
    stands_for: Dict,
    tolerance: int,
    taper: Optional[int],
    name: str = 'text_matches_pattern',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'pattern', pattern)
    object.__setattr__(self, 'stands_for', stands_for)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    if type(self) != type(other):
      return False
    return hash(self) == hash(other)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    if not (isinstance(E, Text)):
      return AtomScore(0)
    local_taper = self.taper
    if local_taper is None:
      local_taper = max(len(E.text), len(self.pattern)) // 2
    assert local_taper >= 0
    error = sa_pattern_edit_distance(E.text, self.pattern, self.stands_for)
    return AtomScore(_taper_error(error, self.tolerance, local_taper))


@dataclass(frozen=True)
class TextPropertiesAre(Degree1Predicate):
  """Says a field's text has the specified properties.

  See the example below for usage. For every option given, the number of
  characters' worth of error is computed. These errors are added up to obtain
  the total measured error.

  Args:
    tolerance: Will score 1 if the measured error is at most this amount.
    taper: The score tapers from 1 to 0 as the measured error (minus the
      tolerance) goes from 0 to taper+1 inclusive. Defaults to 0.5 * len(E.text).

  The following example invocation describes a field whose text is between 3 and
  10 characters long, consisting of the characters 'X', '-', or a digit, such
  that at most 40% of the string is made up of Xs and dashes, such that at most
  10% of the string is made up of twos, and such that at most 3 dashes appear.

  Example code:
    text_properties_are(
      length={'at_least': 3, 'at_most': 10},
      legal_chars="X-0123456789",
      max_char_proportions=[
        {'chars': "X-", 'proportion': 0.4},
        {'chars': "2", 'proportion': 0.1}],
      min_char_counts=[{'chars': "-", count: 3}])
  """

  length: Optional[Dict]
  legal_chars: Optional[str]
  min_char_proportions: Optional[List]
  max_char_proportions: Optional[List]
  min_char_counts: Optional[List]
  max_char_counts: Optional[List]
  tolerance: int
  taper: Optional[int]

  def __init__(
    self,
    length: Optional[Dict],
    legal_chars: Optional[str],
    min_char_proportions: Optional[List],
    max_char_proportions: Optional[List],
    min_char_counts: Optional[List],
    max_char_counts: Optional[List],
    tolerance: int,
    taper: Optional[int],
    name: str = 'text_properties_are',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'length', length)
    object.__setattr__(self, 'legal_chars', legal_chars)
    object.__setattr__(self, 'min_char_proportions', min_char_proportions)
    object.__setattr__(self, 'max_char_proportions', max_char_proportions)
    object.__setattr__(self, 'min_char_counts', min_char_counts)
    object.__setattr__(self, 'max_char_counts', max_char_counts)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    if not isinstance(E, Text):
      return AtomScore(0)

    local_taper = self.taper if self.taper is not None else len(E.text) // 2
    assert local_taper >= 0

    error = 0
    if self.length is not None:
      error += tp_length(E.text, self.length)
    if self.legal_chars is not None:
      error += tp_legal_chars(E.text, self.legal_chars)
    if self.min_char_proportions is not None:
      error += tp_min_char_proportions(E.text, self.min_char_proportions)
    if self.max_char_proportions is not None:
      error += tp_max_char_proportions(E.text, self.max_char_proportions)
    if self.min_char_counts is not None:
      error += tp_min_char_counts(E.text, self.min_char_counts)
    if self.max_char_counts is not None:
      error += tp_max_char_counts(E.text, self.max_char_counts)
    return AtomScore(_taper_error(error, self.tolerance, local_taper))

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    if type(self) != type(other):
      return False
    return hash(self) == hash(other)


def text_properties_are(
    length: Optional[Dict] = None,
    legal_chars: Optional[str] = None,
    min_char_proportions: Optional[List] = None,
    max_char_proportions: Optional[List] = None,
    min_char_counts: Optional[List] = None,
    max_char_counts: Optional[List] = None,
    tolerance: int = 1,
    taper: Optional[int] = None) -> TextPropertiesAre:
  return TextPropertiesAre(
    length, legal_chars, min_char_proportions, max_char_proportions,
    min_char_counts, max_char_counts, tolerance, taper)


@dataclass(frozen=True)
class HaveUnequalText(Predicate):
  """Says that two fields' assignments have unequal texts.

  Scores 0 if the two fields' assignments have equal texts, 1 otherwise.
  """

  def __init__(
    self,
    name: str = 'have_unequal_text',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  @property
  def degree(self) -> int:
    return 2

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities

    if E1.entity_text != E2.entity_text:
      return AtomScore(1)
    else:
      return AtomScore(0)


def line_count_is(score_dict: Dict) -> Predicate:
  return LineCountIs(score_dict)


def word_count_is(score_dict: Dict) -> Predicate:
  return WordCountIs(score_dict)


is_one_line = line_count_is({0: 0, 1: 1, 2: 0})
is_two_lines = line_count_is({1: 0, 2: 1, 3: 0})
is_three_lines = line_count_is({2: 0, 3: 1, 4: 0})
is_four_lines = line_count_is({3: 0, 4: 1, 5: 0})

is_one_word = word_count_is({0: 0, 1: 1, 2: 0})
is_two_words = word_count_is({1: 0, 2: 1, 3: 0})
