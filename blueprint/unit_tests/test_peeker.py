from unittest import TestCase

from bp.peeker import Peeker


class TestPeeker(TestCase):

  def test_peek_distance_1(self) -> None:
    nums = [3, 4, 2, 3, 1]
    iterator = iter(nums)
    self.peeker = Peeker(iterator)

    expected_ordering = [3, 2, 3, 1, 4]
    for i in range(5):
      self.assertEqual(next(self.peeker), expected_ordering[i])
    self.assertRaises(StopIteration, self.peeker.__next__)

  def test_peek_distance_2(self) -> None:
    nums = [3, 4, 2, 3, 1]
    iterator = iter(nums)
    self.peeker = Peeker(iterator, peek_distance=2)

    expected_ordering = [2, 3, 1, 3, 4]
    for i in range(5):
      self.assertEqual(next(self.peeker), expected_ordering[i])
    self.assertRaises(StopIteration, self.peeker.__next__)

  def test_peek_distance_3(self) -> None:
    nums = [3, 4, 2, 3, 1]
    iterator = iter(nums)
    self.peeker = Peeker(iterator, peek_distance=3)

    expected_ordering = [2, 1, 3, 3, 4]
    for i in range(5):
      self.assertEqual(next(self.peeker), expected_ordering[i])
    self.assertRaises(StopIteration, self.peeker.__next__)
