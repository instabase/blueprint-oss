"""Rules defining label-value relationships."""

from .impingement import nothing_between_horizontally, nothing_between_vertically
from .logical import all_hold, any_holds
from .spatial import AlignmentLine, Direction, are_aligned, are_arranged, bottom_aligned_pair, left_to_right_pair


"""
  Says that two fields are a label-value pair going left-to-right.

  This rule says that the two fields are arranged left-to-right, that they are
  bottom-aligned, and that there is nothing between them.

  Example code:
    extract(
      text_equals('Net pay')('label'),
      is_dollar_amount('value'),
      is_left_to_right_label_value_pair('label', 'value'))
"""
is_left_to_right_label_value_pair = all_hold(
  left_to_right_pair(),
  bottom_aligned_pair(),
  nothing_between_horizontally)


_top_down_alignment_tolerance = 1
_top_down_alignment_taper = 3.5


"""
  Says that two fields are a top-down label-value pair.

  This rule says that the two fields are arranged top-down, that they are left-,
  right-, or center-aligned, and that there is nothing between them.

  Similar to `left_to_right_label_value_pair`.

  Example code:
    extract(
      text_equals('Net pay')('label'),
      is_dollar_amount('value'),
      is_top_down_label_value_pair('label', 'value'))
"""
is_top_down_label_value_pair = all_hold(
  are_arranged(Direction.TOP_DOWN, max_distance=2, taper=1),
  nothing_between_vertically,
  any_holds(
    are_aligned(
      AlignmentLine.RIGHT_SIDES,
      tolerance=_top_down_alignment_tolerance,
      taper=_top_down_alignment_taper),
    are_aligned(
      AlignmentLine.LEFT_SIDES,
      tolerance=_top_down_alignment_tolerance,
      taper=_top_down_alignment_taper),
    are_aligned(
      AlignmentLine.VERTICAL_MIDLINES,
      tolerance=_top_down_alignment_tolerance,
      taper=_top_down_alignment_taper)))
