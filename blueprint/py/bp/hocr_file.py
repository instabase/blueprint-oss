"""Generate BP docs from HOCR files."""

from hocr_parser.bbox import BBox as hocr_BBox
from hocr_parser.hocr_document import HOCRDocument
from hocr_parser.hocr_node import HOCRNode

from itertools import chain
from pathlib import Path
from typing import Tuple, Optional

from .build_document import InputPage, InputWord, build_document
from .document import Document
from .entity import Page
from .geometry import BBox, Interval
from .ocr import WordConfidence


def _bbox(vertices: hocr_BBox) -> BBox:
  return BBox(Interval.spanning([vertices.x1, vertices.x2]),
              Interval.spanning([vertices.y1, vertices.y2]))

def _get_input_word_from_hocr_word(word: HOCRNode) -> InputWord:
  if word.bbox is None:
    raise ValueError(f"Node {word} doesn't have a bounding box")
  bbox = _bbox(word.bbox)
  return InputWord(bbox, word.ocr_text, confidence=WordConfidence(
    word_confidence=word.confidence, low_confidence=None, char_confidences=None))


def _get_words_from_page(page: HOCRNode) -> Tuple[InputWord, ...]:
  def get_words_from_paragraph(paragraph: HOCRNode) -> Tuple[InputWord, ...]:
    return tuple(_get_input_word_from_hocr_word(word)
      for word in paragraph.words)
  return tuple(chain.from_iterable(get_words_from_paragraph(paragraph)
    for paragraph in page.paragraphs))


def generate_doc_from_hocr(root: Optional[HOCRNode], name: str) -> Document:
  if root is None:
    raise ValueError(f"No root")
  document_pages = root.pages

  def prepare_input_page(page_number: int, page: HOCRNode) -> InputPage:
    if page.bbox is None:
      raise ValueError(f"Node {page} doesn't have a bounding box")

    input_words = _get_words_from_page(page)
    y_offset = 0
    for i in range(page_number):
      if document_pages[i].bbox is None:
        raise ValueError(f"Node {document_pages[i]} doesn't have a bounding box")
      y_offset += document_pages[i].bbox.y2 - document_pages[i].bbox.y1 # type: ignore

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
  abs_path = path.absolute()
  if not abs_path.exists():
    raise ValueError(f"Input path {path} does not exist")
  if not abs_path.is_file():
    raise ValueError(f"Input path {path} is not a file")
  return generate_doc_from_hocr(HOCRDocument(str(abs_path)).body, path.stem)


def load_doc_from_hocr_string(text: str) -> Document:
  import tempfile
  file = tempfile.NamedTemporaryFile()
  with open(file.name, 'w') as fd:
    fd.write(text)
  return load_doc_from_hocr(Path(file.name))
