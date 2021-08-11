"""Generate BP docs from IBOCR files."""

import itertools
import json
import logging

from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Optional, Tuple

from .build_document import InputPage, InputWord, build_document
from .document import Document
from .entity import Page
from .geometry import BBox, Interval


def _bbox(w: Dict) -> BBox:
  x0: float = w['start_x']
  x1: float = w['end_x']
  y0: float = w['start_y']
  y1: float = w['end_y']
  return BBox(Interval.spanning([x0, x1]),
              Interval.spanning([y0, y1]))


def _get_input_word_from_ibocr_word(ibocr_word: Dict) -> InputWord:
  return InputWord(_bbox(ibocr_word), ibocr_word['word'])


def generate_doc_from_ibocr(raw_json: Any, name: str) -> Document:
  assert raw_json
  # This is assuming that after map records, all of the words are always in
  # this first blob. I'm not sure if this assumption is sound.
  blob = raw_json[0]
  assert(isinstance(blob['metadata_list'], list))
  layouts = blob['metadata_list']
  assert layouts

  def prepare_input_page(page_number: int) -> InputPage:
    # This is all hacky.
    page_layout = layouts[page_number]
    assert isinstance(page_layout['layout']['width'], (int, float))
    assert isinstance(page_layout['layout']['height'], (int, float))
    input_words = tuple(map(
      _get_input_word_from_ibocr_word,
      filter(lambda ibocr_word: ibocr_word['page'] == page_number,
        itertools.chain.from_iterable(blob['lines']))))
    y_offset = sum(layouts[i]['layout']['height'] for i in range(page_number))
    page = Page(
      BBox(
        Interval(0, page_layout['layout']['width']),
        Interval(y_offset, page_layout['layout']['height'] + y_offset)),
      page_number + 1)
    return InputPage(page, input_words)

  input_pages = tuple(prepare_input_page(page_number)
    for page_number in range(len(layouts)))
  return build_document(input_pages, name)
