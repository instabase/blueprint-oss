"""String algorithms.

Some people, when confronted with a problem, think “I know, I'll use regular
expressions.” Now they have two problems.
                                                                Jamie Zawinski
"""

from typing import Dict


def edit_distance(s1: str, s2: str) -> int:
  """The minimum number of edits required to make s1 equal to s2.

  This is also known as the Levenshtein distance.

  An edit is the addition, deletion, or replacement of a character.
  """

  if not s1:
    return len(s2)
  if not s2:
    return len(s1)

  M = [[0 for _ in range(len(s2) + 1)] for _ in range(len(s1) + 1)]
  # M[i1][i2] is the edit distance between s1[:i1] and s2[:i2].
  for i1 in range(len(s1) + 1):
    M[i1][0] = i1
  for i2 in range(len(s2) + 1):
    M[0][i2] = i2

  for i1 in range(1, len(s1) + 1):
    for i2 in range(1, len(s2) + 1):
      cost = 0 if s1[i1 - 1] == s2[i2 - 1] else 1
      M[i1][i2] = min(
          [
              1 + M[i1 - 1][i2],
              1 + M[i1][i2 - 1],
              cost + M[i1 - 1][i2 - 1],
          ])

  return M[len(s1)][len(s2)]


def relative_edit_distance(s1: str, s2: str) -> float:
  """Measures how similar two strings are.

  Returns:
    A number between 0 and 1. Returns 0 if the strings are identical, 1 if the
    strings have nothing in common.
  """

  if not s1 and not s2:
    return 0.0
  return edit_distance(s1, s2) / max(len(s1), len(s2))


def substring_edit_distance(s: str, t: str) -> int:
  """The minimum number of edits required to make t a substring of s.

  An edit is the addition, deletion, or replacement of a character.
  """

  if not s:
    return len(t)
  if not t:
    return 0

  M = [[0 for _ in range(len(t) + 1)] for _ in range(len(s) + 1)]
  # M[i][j] is the minimum number of t-edits required to make t[:j] a suffix of s[:i].
  for i in range(len(s) + 1):
    M[i][0] = 0
  for j in range(len(t) + 1):
    M[0][j] = j

  for i in range(1, len(s) + 1):
    for j in range(1, len(t) + 1):
      cost = 0 if s[i - 1] == t[j - 1] else 1
      M[i][j] = min(
          [
              1 + M[i - 1][j],
              1 + M[i][j - 1],
              cost + M[i - 1][j - 1],
          ])

  return min(M[i][len(t)] for i in range(len(s) + 1))


def pattern_edit_distance(
    s: str, pattern: str, stands_for: Dict[str, str]) -> int:
  """The minimum number of edits required to make s match the pattern.

  An edit is the addition, deletion, or replacement of a character.

  Characters in the pattern are treated as literals, unless they appear in as
  keys in the the stands_for dictionary, in which case they "stand for" any one
  of the values in stands_for[char].

  If stands_for is empty, then this is the Levenshtein distance between s and
  the pattern.

  Args:
    stands_for: A dictinary from character to collection of characters (a
      string). When comparing the entity's text to the given pattern, anytime a
      key in this dictionary appears in the pattern, any of the characters in
      the corresponding dictionary value will be considered a pattern match.

  Example:
    pattern_edit_distance("abc123", "aaazzz", {"z": "23"}) is 3. The "b" and "c"
    need to be changed to "a", and the "1" needs to be changed to a "2" or a "3".
  """

  if not s:
    return len(pattern)
  if not pattern:
    return len(s)

  M = [[0 for _ in range(len(pattern) + 1)] for _ in range(len(s) + 1)]
  # M[i][j] is the pattern edit distance between s[:i] and pattern[:j].
  for i in range(len(s) + 1):
    M[i][0] = i
  for j in range(len(pattern) + 1):
    M[0][j] = j

  for i in range(1, len(s) + 1):
    for j in range(1, len(pattern) + 1):
      if pattern[j - 1] in stands_for:
        cost = 0 if s[i - 1] in stands_for[pattern[j - 1]] else 1
      else:
        cost = 0 if s[i - 1] == pattern[j - 1] else 1
      M[i][j] = min(
          [
              1 + M[i - 1][j],
              1 + M[i][j - 1],
              cost + M[i - 1][j - 1],
          ])

  return M[len(s)][len(pattern)]
