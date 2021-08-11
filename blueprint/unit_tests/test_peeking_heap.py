from unittest import TestCase

from bp.peeking_heap import PeekingHeap


class TestPeekingHeap(TestCase):

  def test_peek_distance_1(self) -> None:
    nums0 = [2, 1, 6]
    nums1 = [8, 5, 1]
    nums2 = [3, 3, 0]
    iterators = [iter(n) for n in [nums0, nums1, nums2]]
    self.peeking_heap = PeekingHeap(iterators, lambda x: x)

    expected_ordering = [1, 2, 3, 0, 3, 6, 5, 1, 8]
    for i in range(9):
      self.assertEqual(next(self.peeking_heap), expected_ordering[i])
    self.assertRaises(StopIteration, self.peeking_heap.__next__)

  def test_peek_distance_2(self) -> None:
    nums0 = [2, 1, 6]
    nums1 = [8, 5, 1]
    nums2 = [3, 3, 0]
    iterators = [iter(n) for n in [nums0, nums1, nums2]]
    self.peeking_heap = PeekingHeap(iterators, lambda x: x, peek_distance=2)

    expected_ordering = [1, 2, 0, 3, 3, 1, 5, 6, 8]
    for i in range(9):
      self.assertEqual(next(self.peeking_heap), expected_ordering[i])
    self.assertRaises(StopIteration, self.peeking_heap.__next__)
