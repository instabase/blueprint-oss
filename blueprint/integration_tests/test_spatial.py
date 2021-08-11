from unittest import TestCase

from .mock_doc import mock_doc
from .testing import ExpectedExtraction, no_nontrivial_extractions

from bp.rules.spatial import bottom_aligned, left_aligned, left_to_right, right_aligned, top_down
from bp.rules.textual import TextEquals
from bp.tree import combine, extract


class TestSpatialRules(TestCase):

  def test_row_column(self) -> None:
    doc = mock_doc([
      """
      Apple     Orange  Banana
      """
    ])

    expected_extraction = ExpectedExtraction(
        doc, {
            'apple': 'Apple',
            'orange': 'Orange',
            'banana': 'Banana',
        })

    self.assertTrue(
        expected_extraction.is_exactly_best_extraction_from(
            extract(
              left_to_right('apple', 'orange', 'banana'))))

    self.assertTrue(
        expected_extraction.is_exactly_best_extraction_from(
            combine(
              extract(
                TextEquals(('Peach',))('peach'),
                field_types={'peach': 'Text'},),
              extract(
                left_to_right('apple', 'orange', 'banana')))))

    self.assertTrue(
        no_nontrivial_extractions(
            doc,
            extract(
              top_down('apple', 'orange', 'banana'))))

  def test_table(self) -> None:
    doc = mock_doc([
      """
      Apple   Orange   Banana

      Peach   Cherry   Mango
      """
    ])

    expected_extraction = ExpectedExtraction(doc, {
      'apple': 'Apple',
      'orange': 'Orange',
      'banana': 'Banana',
      'peach': 'Peach',
      'cherry': 'Cherry',
      'mango': 'Mango',
    })

    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        extract(
            left_to_right('apple', 'orange', 'banana'),
            left_to_right('peach', 'cherry', 'mango'),
            bottom_aligned('apple', 'orange', 'banana'),
            bottom_aligned('peach', 'cherry', 'mango'),
            top_down('apple', 'peach'),
            top_down('orange', 'cherry'),
            top_down('banana', 'mango'),
            left_aligned('apple', 'peach'),
            left_aligned('orange', 'cherry'),
            left_aligned('banana', 'mango'))))

  def test_alignment(self) -> None:
    doc = mock_doc([
      """
      Apple

      Mango
      """])

    expected_extraction = ExpectedExtraction(doc, {
      'apple': 'Apple',
      'mango': 'Mango',
    })

    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        extract(
            top_down('apple', 'mango'),
            left_aligned('apple', 'mango'))))

    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        extract(
            top_down('apple', 'mango'),
            right_aligned('apple', 'mango'))))

    self.assertTrue(
      expected_extraction.is_exactly_best_extraction_from(
        extract(
            top_down('apple', 'mango'),
            left_aligned('apple', 'mango'),
            right_aligned('apple', 'mango'))))
