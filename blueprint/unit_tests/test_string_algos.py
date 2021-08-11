from unittest import TestCase

from bp.string_algos import *


class TestStringAlgos(TestCase):

  def test_substring_edit_distance(self) -> None:
    self.assertEqual(2, substring_edit_distance("abcdefg", "aaa"))
    self.assertEqual(0, substring_edit_distance("abcdefg", "def"))
    self.assertEqual(1, substring_edit_distance("abcdefg", "deg"))
    self.assertEqual(3, substring_edit_distance("", "abc"))
    self.assertEqual(0, substring_edit_distance("abc", ""))

  def test_pattern_edit_distance(self) -> None:
    self.assertEqual(3, pattern_edit_distance("abc123", "aaazzz", {"z": "23"}))
    self.assertEqual(2, pattern_edit_distance("aaaaa", "aaa", {}))
    self.assertEqual(
        0,
        pattern_edit_distance(
            "XXX-xx-12X4",
            "XXX-XX-9999",
            {
              "X": "Xx",
              "9": "X1234"
            }))
