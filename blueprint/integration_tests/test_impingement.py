from unittest import TestCase

from .mock_doc import mock_doc
from .testing import ExpectedExtraction, no_nontrivial_extractions

from bp.rules.impingement import nothing_between_vertically_custom
from bp.rules.spatial import top_down
from bp.rules.textual import text_equals
from bp.tree import extract


class TestImpingement(TestCase):

  def test_impingement_intervals(self) -> None:
    doc = mock_doc([
      """
      Pineapple

          Apple

      Pear
      """
    ])

    expected_extraction = ExpectedExtraction(
      doc,
      {
        'pineapple': 'Pineapple',
        'pear': 'Pear',
        'apple': 'Apple',
      })

    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        extract(
            text_equals('Apple')('apple'),
            top_down('pineapple', 'pear'),
            nothing_between_vertically_custom(maximum_impingement=0.5)
              ('pineapple', 'pear'))))

    self.assertTrue(
      no_nontrivial_extractions(
        doc,
        extract(
            text_equals('Apple')('apple'),
            top_down('pineapple', 'pear'),
            nothing_between_vertically_custom(spanning=True,
                                              maximum_impingement=0.5)
              ('pineapple', 'pear'))))
