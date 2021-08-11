from unittest import TestCase

from bp.functional import *


class TestFunctional(TestCase):

  def test_all_equal(self) -> None:
    self.assertTrue(
      all_equal([1, 1, 1, 1]))

    self.assertFalse(
      all_equal([1, 2, 3]))

    self.assertTrue(
      all_equal([]))

    def explode() -> int:
      raise Exception

    # Test short-circuiting.
    self.assertFalse(
      all_equal(
        explode() if i == 2 else i
        for i in range(3)))
