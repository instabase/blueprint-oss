from unittest import TestCase

from .mock_doc import mock_doc
from .testing import ExpectedExtraction, no_nontrivial_extractions, times_out

from bp.rules.semantic import IsDate, IsDollarAmount
from bp.rules.textual import text_equals
from bp.run import run_model
from bp.tree import combine, extract, pick_best


class TestExtraction(TestCase):

  def _test_runtime(self) -> None:
    """Confirm that pattern() runs fast given the correct input field order."""

    N = 30 # 30! = 265252859812191058636308480000000
    doc = mock_doc([
      """
      Foo Bar
      """ +
      """
      Foo
      """ * N
    ])

    # Our extraction consists of a bunch of "foo" fields and a single "bar"
    # field, such that all of them are in one big column. There are N!
    # (factorial) extractions of just the foo fields, none of which will work
    # because there is only one assignment of the bar field, and it is not in a
    # column with the foo fields.

    foo_fields = tuple(f'foo_{i}' for i in range(N))

    rules = (
      *(text_equals('Foo')(field) for field in foo_fields),
      text_equals('Bar')('bar'),
      # list(left_aligned_column(*foo_fields, 'bar', ordered=False)),
    )

    # Shouldn't time out if tree is auto-ordered.
    self.assertFalse(
        times_out(3, lambda: \
            run_model(
              doc,
              extract(*rules)
            )))

  def test_masses(self) -> None:

    doc = mock_doc([
      """
      Apple    Orange   Banana
      """])

    pattern_1 = extract(
      text_equals("Apple")("F1"))
    pattern_2 = extract(
      text_equals("Bana")("F3"),
      text_equals("Orange")("F2"))
    root = pick_best(pattern_1, pattern_2)

    expected_extraction = ExpectedExtraction(doc,
      {
        "F2": "Orange",
        "F3": "Banana",
      })
    self.assertTrue(expected_extraction.is_exactly_best_extraction_from(root))
