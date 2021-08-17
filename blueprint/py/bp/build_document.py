"""Build a Document from a collection of words."""

import dataclasses
import logging

from functools import lru_cache
from itertools import chain
from statistics import median
from typing import Any, Iterable, List, Optional, Tuple

from .bp_logging import bp_logging
from .document import DocRegion, Document, EZDocRegion
from .entity import Entity, Page, Text, Word
from .functional import take_before, without_none
from .geometry import BBox, Interval
from .ocr import InputWord

from .entity_gen.clustering import build_multiline_clusters, build_words_and_phrases
from .entity_gen.dates import get_dates
from .entity_gen.dollar_amounts import get_dollar_amounts


@dataclasses.dataclass
class InputPage:
  page: Page
  words: Tuple[InputWord, ...]
  msrapi_lines: Tuple[Tuple[InputWord, ...], ...] = tuple()


@dataclasses.dataclass
class PageEntities:
  words: Tuple[Entity, ...]
  maximal_phrases: Tuple[Entity, ...]
  sub_phrases: Tuple[Entity, ...]
  multiline_clusters: Tuple[Entity, ...]

  @staticmethod
  def combine(page_entities: Tuple['PageEntities', ...]) -> 'PageEntities':
    return PageEntities(
      tuple(chain.from_iterable(P.words for P in page_entities)),
      tuple(chain.from_iterable(P.maximal_phrases for P in page_entities)),
      tuple(chain.from_iterable(P.sub_phrases for P in page_entities)),
      tuple(chain.from_iterable(P.multiline_clusters for P in page_entities)))


def build_document(
    input_pages: Tuple[InputPage, ...], name: str) -> Document:
  """Build a Document from a tuple of pages and their words.

  For input documents with multiple pages, we assume the pages to be
  left-aligned: the bounding box of each page in the resulting Document has
  x-interval (0, page_width) and y-interval (offset, page_height + offset),
  where offset is the sum of of the heights of all previous pages in the
  document.

  Args:
    input_pages: The pages of the document and the words on those pages.
      The pages should be given in order.
    name: The name of the document.
  """

  sorted_page_numbers = tuple(
    input_page.page.page_number for input_page in input_pages)

  def y_offset(page: Page) -> float:
    previous_pages = take_before(
      lambda other_page: other_page == page,
      (input_page.page for input_page in input_pages))
    return sum(page.bbox.height for page in previous_pages)

  def build_page_entities(input_page: InputPage) -> PageEntities:
    page = input_page.page
    input_words = input_page.words
    msrapi_lines = input_page.msrapi_lines

    def make_word(input_word: InputWord) -> Optional[Word]:
      def offset(input_word: InputWord) -> InputWord:
        def offset_bbox(bbox: BBox) -> BBox:
          return BBox(
            bbox.ix,
            Interval(
              bbox.iy.a + y_offset(page),
              bbox.iy.b + y_offset(page)))
        return dataclasses.replace(
          input_word, bbox=offset_bbox(input_word.bbox))

      input_word = offset(input_word)

      def sanity_check(input_word: InputWord) -> bool:
        if not page.bbox.contains_bbox(input_word.bbox):
          bp_logging.warning(
            '{} not in page bounds {}; discarding'.format(input_word, page.bbox))
          return False
        if not input_word.text:
          bp_logging.warning('{} has empty text; discarding'.format(input_word))
          return False
        return True

      if sanity_check(input_word):
        return Word.from_input_word(input_word)
      else:
        return None

    if msrapi_lines:
      if input_words:
        raise RuntimeError('Mixing MSRAPI mode with normal clustering mode')

      words: List[Entity] = []
      msrapi_line_entities: List[Entity] = []

      for msrapi_line in msrapi_lines:
        if msrapi_line:
          if len(msrapi_line) == 1:
            word = make_word(msrapi_line[0])
            if word:
              text = Text.from_words((word, ), maximality_score=1)
              words.append(text)
              msrapi_line_entities.append(text)
          else:
            words_in_line = tuple(without_none(map(make_word, msrapi_line)))
            if len(words_in_line) == len(msrapi_line):
              for word in words_in_line:
                words.append(Text.from_words((word, ), maximality_score=0))
              msrapi_line_entities.append(Text.from_words(words_in_line,
                                                     maximality_score=1))
            else:
              bp_logging.warning(f'Some words from {msrapi_line} were out ' +
                                 f'of page bounds; discarding entire line')

      return PageEntities(
        tuple(words),
        tuple(msrapi_line_entities),
        sub_phrases=tuple(),
        multiline_clusters=tuple())

    else:
      word_entities = tuple(without_none(map(make_word, input_words)))
      word_texts = tuple(Text.from_words((word, )) for word in word_entities)
      words_and_phrases = build_words_and_phrases(word_texts, page, document)
      maximal_phrases = get_maximal_phrases(words_and_phrases)
      scored_words = tuple(filter(lambda T: len(T.words) == 1, words_and_phrases))
      sub_phrases = tuple(frozenset(words_and_phrases) - frozenset(maximal_phrases))
      # Not including multiline clusters for now.
      multiline_clusters: Tuple[Entity, ...] = tuple()
      return PageEntities(
        scored_words,
        maximal_phrases,
        sub_phrases,
        multiline_clusters)

  def get_maximal_phrases(phrases: Tuple[Text, ...]) -> Tuple[Text, ...]:
    return tuple(filter(lambda T: T.maximality_score == 1, phrases))

  document = Document.from_entities(
    (input_page.page for input_page in input_pages), name=name)

  page_numbers = tuple(input_page.page.page_number for input_page in input_pages)
  page_entities = PageEntities.combine(tuple(
    build_page_entities(input_page) for input_page in input_pages))
  entity_pool = tuple(frozenset(
    tuple(chain(page_entities.words, page_entities.maximal_phrases,
      page_entities.sub_phrases))))

  dollar_amounts = tuple(frozenset(get_dollar_amounts(entity_pool)))
  dates = tuple(frozenset(get_dates(entity_pool)))

  return document.with_entities(
    frozenset(chain(page_entities.words, page_entities.maximal_phrases,
      page_entities.sub_phrases, page_entities.multiline_clusters,
      dates, dollar_amounts)))
