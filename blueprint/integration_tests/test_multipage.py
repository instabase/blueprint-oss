from unittest import TestCase

from .mock_doc import mock_doc
from .testing import ExpectedExtraction, raises_exception

from bp.tree import extract

from bp.rules.logical import *
from bp.rules.spatial import *
from bp.rules.textual import *

class TestMultipage(TestCase):

  def test_multipage_doc(self) -> None:

    doc = mock_doc([
      """

      Page number:   1

      """,
      """

      Page number:   2

      """,
      """

      Page number:   3

      """,
    ])

    expected_extraction = ExpectedExtraction(
      doc,
      {
        'page_number_label_1': 'Page number:',
        'page_number_1': '1',
        'page_number_label_2': 'Page number:',
        'page_number_2': '2',
        'page_number_label_3': 'Page number:',
        'page_number_3': '3',
      })

    self.assertTrue(expected_extraction.is_exactly_best_extraction_from(
      extract(
          text_equals('Page number:')('page_number_label_1'),
          text_equals('Page number:')('page_number_label_2'),
          text_equals('Page number:')('page_number_label_3'),
          top_down('page_number_label_1', 'page_number_label_2'),
          PageNumberIs({2: 0, 3: 1, 4: 0})('page_number_label_3'),

          bottom_aligned('page_number_label_1', 'page_number_1'),
          left_to_right('page_number_label_1', 'page_number_1'),

          bottom_aligned('page_number_label_2', 'page_number_2'),
          left_to_right('page_number_label_2', 'page_number_2'),

          bottom_aligned('page_number_label_3', 'page_number_3'),
          left_to_right('page_number_label_3', 'page_number_3'),
    )))
