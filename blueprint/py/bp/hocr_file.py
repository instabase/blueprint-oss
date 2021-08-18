"""Generate BP docs from HOCR files."""

import hocr_parser.bbox
from hocr_parser.hocr_document import HOCRDocument
from hocr_parser.hocr_node import HOCRNode

from itertools import chain
from pathlib import Path
from typing import Dict, Tuple

from .build_document import InputPage, InputWord, build_document
from .document import Document
from .entity import Page
from .geometry import BBox, Interval

def _bbox(vertices: hocr_parser.bbox.BBox) -> BBox:
  return BBox(Interval.spanning([vertices.x1, vertices.x2]),
              Interval.spanning([vertices.y1, vertices.y2]))

def _get_input_word_from_hocr_word(word: HOCRNode) -> InputWord:
  bbox = _bbox(word.bbox)
  return InputWord(bbox, word.text, confidence=word.confidence)


def _get_words_from_page(page: HOCRNode) -> Tuple[InputWord, ...]:
  def get_words_from_paragraph(paragraph: HOCRNode) -> Tuple[InputWord, ...]:
    return tuple(_get_input_word_from_hocr_word(word)
      for word in paragraph.words)
  return tuple(chain.from_iterable(get_words_from_paragraph(paragraph)
    for paragraph in page.paragraphs))


def generate_doc_from_hocr(root: HOCRNode, name: str) -> Document:
  document_pages = root.pages

  def prepare_input_page(page_number: int, page: Dict) -> InputPage:
    input_words = _get_words_from_page(page)
    y_offset = sum(document_pages[i].bbox.y2 - document_pages[i].bbox.y1 for i in range(page_number))
    bp_page = Page(
      BBox(
        Interval(0, page.bbox.x2 - page.bbox.x1),
        Interval(y_offset, page.bbox.y2 - page.bbox.y1 + y_offset)),
      page_number + 1)
    return InputPage(bp_page, input_words)

  input_pages = tuple(prepare_input_page(page_number, page)
    for page_number, page in enumerate(document_pages))
  return build_document(input_pages, name)


def load_doc_from_hocr(path: Path) -> Document:
  return generate_doc_from_hocr(HOCRDocument(path).body, path.stem)
