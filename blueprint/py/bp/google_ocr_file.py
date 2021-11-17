"""Generate BP docs from Google Cloud Vision OCR files."""

import json
import logging

from itertools import chain
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

from .build_document import InputPage, InputWord, build_document
from .document import Document
from .entity import Page
from .geometry import BBox, Interval


def _bbox(vertices: List[Dict]) -> BBox:
  if len(vertices) != 4:
    raise ValueError(f'invalid vertices {vertices}, must be length 4')
  x0: float = vertices[0]['x']
  x1: float = vertices[1]['x']
  y0: float = vertices[0]['y']
  y1: float = vertices[2]['y']
  return BBox(Interval.spanning([x0, x1]),
              Interval.spanning([y0, y1]))


def _get_input_word_from_google_word(word: Dict) -> InputWord:
  bbox = _bbox(word['boundingBox']['vertices'])
  text = ''.join(symbol['text'] for symbol in word['symbols'])
  return InputWord(bbox, text)


def _get_words_from_page(page: Dict) -> Tuple[InputWord, ...]:
  def get_words_from_paragraph(paragraph: Dict) -> Tuple[InputWord, ...]:
    return tuple(_get_input_word_from_google_word(word)
      for word in paragraph['words'])
  def get_words_from_block(block: Dict) -> Tuple[InputWord, ...]:
    return tuple(chain.from_iterable(get_words_from_paragraph(paragraph)
      for paragraph in block['paragraphs']))
  return tuple(chain.from_iterable(get_words_from_block(block)
    for block in page['blocks']))


def generate_doc_from_google_ocr_json(raw_json: Dict, name: str) -> Document:
  document_pages = raw_json['fullTextAnnotation']['pages']

  def prepare_input_page(page_number: int, page: Dict) -> InputPage:
    input_words = _get_words_from_page(page)
    y_offset = sum(document_pages[i]['height'] for i in range(page_number))
    bp_page = Page(
      BBox(
        Interval(0, page['width']),
        Interval(y_offset, page['height'] + y_offset)),
      page_number + 1)
    return InputPage(bp_page, input_words)

  input_pages = tuple(prepare_input_page(page_number, page)
    for page_number, page in enumerate(document_pages))
  return build_document(input_pages, name)


def load_doc_from_google_ocr(path: Path) -> Document:
  with path.open('rb') as f:
    f_str = f.read()
    data = f_str.decode("utf-8", errors='ignore')
    return generate_doc_from_google_ocr_json(json.loads(data), path.stem)
