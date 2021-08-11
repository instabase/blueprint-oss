from unittest import TestCase

from bp.extraction import OverlappingFieldsError
from bp.rules.logical import Nop
from bp.tree import MergeNode, combine, extract


class TestValidation(TestCase):
  """Test extraction tree validation processes."""

  def test_merge_validation(self) -> None:
    with self.assertRaises(OverlappingFieldsError):
      MergeNode.validate(MergeNode((
        extract(
          Nop()('f1'), Nop()('f_int'),
          field_types={'f1': 'text', 'f_int': 'text'}),
        extract(
          Nop()('f2'), Nop()('f_int'),
          field_types={'f2': 'text', 'f_int': 'text'}))))
