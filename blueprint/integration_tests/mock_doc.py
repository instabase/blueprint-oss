"""Mock documents, used for integration testing."""

from dataclasses import dataclass, replace
from itertools import chain
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from bp.document import Document
from bp.entity import Page
from bp.build_document import InputPage, build_document
from bp.geometry import BBox, Interval
from bp.ocr import InputWord


MockWord = Tuple[str, Tuple[float, float], Tuple[float, float]]


def _input_word(mock_word: MockWord) -> InputWord:
  bbox = BBox(
    Interval(mock_word[1][0], mock_word[1][1]),
    Interval(mock_word[2][0], mock_word[2][1]))
  return InputWord(bbox, mock_word[0], None, None, None)


@dataclass(frozen=True)
class MockPage:
  """A mock page.
  Args:
    mock_words: The mock words on the page.
    bbox: The bounding box of the mock page.
  """

  words: Tuple[InputWord, ...]
  bbox: BBox


def mock_doc(pages: Sequence[str],
             name: Optional[str] = None) -> Document:
  """A mock doc described as an ASCII drawing.
  Args:
    pages: Every string represents a page of input. See the test code for
      examples.
    name: A name for the Document. This is mostly for logging/debugging. It
      should usually be fine to use the default.
  """

  if not pages:
    pages = [""]

  mock_pages: List[MockPage] = []
  offset = 0.0
  for page in pages:
    mock_words: List[MockWord] = []
    lines = page.split('\n')
    for line_no, line in enumerate(lines):
      start: Optional[int] = None
      for i in range(len(line) + 1):
        if i < len(line) and line[i] != ' ':
          if start is None:
            start = i
        if i == len(line) or line[i] == ' ':
          if start is not None:
            word = line[start:i]
            mock_word = (
              word,
              (start, i),
              (line_no, line_no + 1))
            mock_words += [mock_word]
            start = None
    page_width = max(len(line) for line in lines) if lines else 0
    mock_pages += [
      MockPage(tuple(map(lambda W: _input_word(W), mock_words)),
               BBox(Interval(0, page_width),
                    Interval(0 + offset, len(lines) + offset)))]
    offset += len(lines)

  assert len(pages) == len(mock_pages)
  if name is None:
    name = ('---page break---').join(pages)
  return build_mock_doc(tuple(mock_pages), name=name)


def build_mock_doc(mock_pages: Tuple[MockPage, ...], name: str) -> Document:
  input_pages = tuple(InputPage(Page(mock_page.bbox, index + 1), mock_page.words)
    for index, mock_page in enumerate(mock_pages))
  return build_document(input_pages, name)
