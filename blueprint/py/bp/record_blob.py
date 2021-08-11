"""Generate BP docs from record blobs."""

from typing import Any, Dict, List, Union

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


def _get_input_word_from_word_poly_dict(word_poly_dict: Dict) -> InputWord:
  return InputWord(_bbox(word_poly_dict), word_poly_dict['word'])


def generate_doc_from_record_blob(blob: Dict, record_name: str) -> Document:
  assert(isinstance(blob['layouts'], dict))
  assert(isinstance(blob['lines'], list))

  layouts: Dict[Union[str, int], Dict] = blob['layouts']
  lines: List[List[Any]] = blob['lines']
  words = [word for line in lines for word in line]
  page_numbers = set(word['page'] for word in words)
  sorted_page_numbers: List[int] = sorted(list(page_numbers))
  msrapi_mode = is_msrapi_lines_mode(lines)

  def get_layout(page_number: int) -> Dict:
    # UGHHHHHHHHHH.

    try:
      return layouts[str(page_number)]
    except:
      pass

    try:
      return layouts[page_number]
    except:
      pass

    raise RuntimeError(f'Could not read layout for page {page_number}')

  def get_page(page_number: int) -> Page:
    layout = get_layout(page_number)
    assert isinstance(layout['width'], (int, float))
    assert isinstance(layout['height'], (int, float))
    y_offset = sum(get_layout(other_page_number)['height']
                   for other_page_number in sorted_page_numbers
                   if other_page_number < page_number)
    return Page(
      BBox(
        Interval(0, layout['width']),
        Interval(y_offset, layout['height'] + y_offset),
      ),
      page_number,
    )

  def prepare_page(page_number: int) -> InputPage:
    page = get_page(page_number)
    if msrapi_mode:
      msrapi_lines = tuple(
        tuple(_get_input_word_from_word_poly_dict(word) for word in line)
        for line in lines if line and line[0]['page'] == page_number
      )
      return InputPage(page, tuple(), msrapi_lines)
    else:
      input_words = tuple(map(
        _get_input_word_from_word_poly_dict,
        filter(lambda word: word['page'] == page_number, words)))
      return InputPage(page, input_words)

  pages = tuple(prepare_page(page_number)
                for page_number in sorted_page_numbers)
  return build_document(pages, record_name)


def is_msrapi_lines_mode(lines: List[List[Any]]) -> bool:
  for line_number in range(len(lines)):
    if line_number % 2 == 0:
      if not lines[line_number]:
        return False
    else:
      if lines[line_number]:
        return False
  return True
