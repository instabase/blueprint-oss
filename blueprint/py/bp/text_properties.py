"""Functions for measuring text adherence to various properties.

This is only used by blueprint.rules.textual, and probably shouldn't be
alongside our core code.
"""

from typing import Dict, List


def length(s: str, d: Dict) -> int:
  assert isinstance(d, Dict)
  assert d.keys() <= {"at_least", "at_most"} or d.keys() == {"exactly"}
  errors = 0
  if "at_most" in d:
    errors += max(0, len(s) - d["at_most"])
  if "at_least" in d:
    errors += max(0, d["at_least"] - len(s))
  if "exactly" in d:
    errors += abs(d["exactly"] - len(s))
  return errors


def legal_chars(s: str, chars: str) -> int:
  return sum(1 for c in s if c not in chars)


def min_char_proportions(s: str, l: List) -> int:
  assert isinstance(l, List)
  error = 0
  for d in l:
    assert isinstance(d, Dict)
    assert d.keys() == {"chars", "proportion"}
    assert isinstance(d["chars"], str)
    error += max(
        0,
        len(s) * d["proportion"] - sum(1 for c in s if c in d["chars"]))
  return error


def max_char_proportions(s: str, l: List) -> int:
  assert isinstance(l, List)
  error = 0
  for d in l:
    assert isinstance(d, Dict)
    assert d.keys() == {"chars", "proportion"}
    assert isinstance(d["chars"], str)
    error += max(
        0,
        sum(1 for c in s if c in d["chars"]) - len(s) * d["proportion"])
  return error


def min_char_counts(s: str, l: List) -> int:
  assert isinstance(l, List)
  error = 0
  for d in l:
    assert isinstance(d, Dict)
    assert d.keys() == {"chars", "count"}
    assert isinstance(d["chars"], str)
    error += max(0, d["count"] - sum(1 for c in s if c in d["chars"]))
  return error


def max_char_counts(s: str, l: List) -> int:
  assert isinstance(l, List)
  error = 0
  for d in l:
    assert isinstance(d, Dict)
    assert d.keys() == {"chars", "count"}
    assert isinstance(d["chars"], str)
    error += max(0, sum(1 for c in s if c in d["chars"]) - d["count"])
  return error
