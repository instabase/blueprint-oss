"""Rules for describing tabular layouts."""

from dataclasses import dataclass
from itertools import chain
from typing import Iterable, Optional, Tuple

from ..document import DocRegion, Document, Entity
from ..extraction import Field
from ..functional import all_equal, pairs, without_none
from ..geometry import BBox, Interval
from ..rule import Conjunction, Disjunction, Predicate, Rule

from .impingement import BoxUnimpinged, IMPINGEMENT_LARGE_INSET, IMPINGEMENT_SMALL_INSET, no_words_between_horizontally, no_words_between_vertically
from .logical import all_hold
from .spatial import AlignmentLine, Orientation, are_aligned, bottom_aligned, left_aligned, left_to_right, one_to_two_lines_above, right_aligned, top_down, top_down_pair


@dataclass(frozen=True)
class TabularHeaderBoxUnimpinged(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'tabular_header_box_unimpinged',
  ):
    super().__init__(
      name = name,
      direction = Orientation.HORIZONTAL,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _tabular_header(doc, E1, E2)


def _tabular_header(doc: Document, E1: Entity, E2: Entity) \
    -> Optional[DocRegion]:
  """
  Says that the first field is a top header for the second.

  Checks that the two fields are arranged top-down, and that the space marked by
  Xs is horizontally unimpinged.

    (First field)  XXXXXXXXXXXXXXXXXXXX
                     (Some other field)          <- This is allowed.
                         (Second field)

  Example code:
    # For the above diagram
    is_tabular_header('first_field', 'second_field')
  """
  return DocRegion.build(doc, BBox.build(
    Interval.spanning_intervals([
      E1.bbox.ix,
      E2.bbox.ix]) \
        .eroded(IMPINGEMENT_LARGE_INSET * doc.median_line_height()),
    E1.bbox.iy \
      .eroded(IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


is_tabular_header = all_hold(
  top_down_pair(),
  TabularHeaderBoxUnimpinged())


@dataclass(frozen=True)
class ImmediateHeaderBoxUnimpinged(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'immediate_header_box_unimpinged',
  ):
    super().__init__(
      name = name,
      direction = Orientation.HORIZONTAL,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _immediate_header(doc, E1, E2)


def _immediate_header(doc: Document, E1: Entity, E2: Entity) \
    -> Optional[DocRegion]:
  """
  Says that the first field is a top header for the second, and that there are
  no rows between them.

  Checks that the two fields are arranged top-down, with the header one or two
  lines above the value, such that the space marked by Xs is horizontally
  unimpinged.

    (First field) XXXXXXXXXXXXXXXXXXXXXXX
    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
                           (Second field)
  """
  return DocRegion.build(doc, BBox.build(
      Interval.spanning_intervals([
          E1.bbox.ix,
          E2.bbox.ix]) \
            .eroded(IMPINGEMENT_LARGE_INSET * doc.median_line_height()),
      Interval.spanning([
        E1.bbox.iy.a,
        E2.bbox.iy.a]) \
          .eroded(0.33 * doc.median_line_height())))


is_immediate_header = all_hold(
  one_to_two_lines_above,
  ImmediateHeaderBoxUnimpinged())


@dataclass(frozen=True)
class TabularEntryBoxUnimpinged(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'tabular_entry_box_unimpinged',
  ):
    super().__init__(
      name = name,
      direction = Orientation.HORIZONTAL,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _tabular_entry_breadth(doc, E1, E2)


def _tabular_entry_breadth(doc: Document, E1: Entity, E2: Entity) \
    -> Optional[DocRegion]:
  """
  Says that the second field is a tabular value underneath the second.

  Checks that the two fields are arranged top-down, and that the space marked by
  Xs is horizontally unimpinged.

    (First field)        (Something else)         <- This is allowed.
    (Again something else)                        <- This too.
    XXXXXXXXXXXXXXXXXXXXXX (Second field)
  """
  return DocRegion.build(doc, BBox.build(
    Interval.spanning_intervals([
      E1.bbox.ix,
      E2.bbox.ix]) \
        .eroded(IMPINGEMENT_LARGE_INSET * doc.median_line_height()),
    E2.bbox.iy.eroded(
        IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


heads_tabular_entry = all_hold(
    top_down_pair(),
    TabularEntryBoxUnimpinged())


def _validate_tabular_fields(fields: Tuple[Field, ...]) -> Tuple[Field, ...]:
  for field in fields:
    if not isinstance(field, Field):
      raise TypeError(
        f'row/column field {field} should have type Field, '
        f'not {type(field)}')
  return fields


def row(*fields: Field, ordered: bool=True) -> Rule:
  """Says that some fields are arranged in a (bottom-aligned) row.

  Args:
    fields: The fields.
    ordered: Whether the left-to-right order in the row is the same as the order
      in which the fields are given.
  """
  if len(fields) < 2:
    raise ValueError('row must take at least 2 fields')
  fields = _validate_tabular_fields(fields)
  alignment_rules = bottom_aligned(*fields)
  if ordered:
    return Conjunction(rules=(alignment_rules, left_to_right(*fields)))
  else:
    return alignment_rules


def left_aligned_column(*fields: Field, ordered: bool=True) -> Rule:
  """Says that some fields are arranged in a left-aligned column.

  Args:
    fields: The fields.
    ordered: Whether the top-down order in the column is the same as the order
      in which the fields are given.
  """
  if len(fields) < 2:
    raise ValueError('left_aligned_column must take at least 2 fields')
  fields = _validate_tabular_fields(fields)
  alignment_rules = left_aligned(*fields)
  if ordered:
    return Conjunction(rules=(alignment_rules, top_down(*fields)))
  else:
    return alignment_rules


def right_aligned_column(*fields: Field, ordered: bool=True) -> Rule:
  """Says that some fields are arranged in a right-aligned column.

  Args:
    fields: The fields.
    ordered: Whether the top-down order in the column is the same as the order
      in which the fields are given.
  """
  if len(fields) < 2:
    raise ValueError('right_aligned_column must take at least 2 fields')
  fields = _validate_tabular_fields(fields)
  alignment_rules = right_aligned(*fields)
  if ordered:
    return Conjunction(rules=(alignment_rules, top_down(*fields)))
  else:
    return alignment_rules


def column(*fields: Field, ordered: bool=True) -> Rule:
  """Says that some fields are arranged in a column.

  The fields may be right-aligned or left-aligned.

  Args:
    fields: The fields.
    ordered: Whether the top-down order in the column is the same as the order
      in which the fields are given.
  """
  if len(fields) < 2:
    raise ValueError('column must take at least 2 fields')
  fields = _validate_tabular_fields(fields)
  alignment_rules = Disjunction(
    rules=(left_aligned(*fields), right_aligned(*fields)))
  if ordered:
    return Conjunction(rules=(alignment_rules, top_down(*fields)))
  else:
    return alignment_rules


def table(rows: Iterable[Iterable[Optional[Field]]]) -> Rule:
  """Says that some fields are arranged in a table.

  Args:
    rows: Lists-of-lists of (optional) fields, in the left-to-right order that
      they appear in the rows. The rows should be given in the top-down order
      that they appear in the table.

  Example code:
    extract(
      is_dollar_amount('period_gross'),
      is_dollar_amount('period_net'),
      # ...
      table([
        [None,          'period_label', 'ytd_label'],
        ['gross_label', 'period_gross', 'ytd_gross'],
        ['net_label',   'period_net',   'ytd_net'],
      ]),
    )
  """
  rows_ = tuple(tuple(row_) for row_ in rows)
  if not all_equal(len(row_) for row_ in rows_):
    raise ValueError('table rows must all have the same length')

  for row_ in rows_:
    for field in row_:
      if not isinstance(field, Field) and field is not None:
        raise TypeError(
          f'table field {field} should be of type Field or None, '
          f'but got type {type(field)}')

  def build_row(row_: Tuple[Optional[Field], ...]) -> Rule:
    fields: Tuple[Field, ...] = tuple(
      field for field in row_ if field is not None)
    return row(*fields)

  def build_column(column_: Tuple[Optional[Field], ...]) -> Rule:
    fields: Tuple[Field, ...] = tuple(
      field for field in column_ if field is not None)
    return column(*fields)

  return Conjunction(tuple(chain(
    map(build_row, rows_),
    map(build_column, zip(*rows_)))))


def tabular_row(*fields: Field) -> Rule:
  """Says that some fields are arranged in a tabular row.

  The first field is considered the label. A "tabular" row has the property that
  there are no words between the label and any entry in the row.

  The fields will be pairwise bottom-aligned.
  """
  return Conjunction(tuple(chain(
    (no_words_between_horizontally(fields[0], F) for F in fields[1:]),
    (row(*fields),),
  )))


def tabular_column(*fields: Field) -> Rule:
  """Says that some fields are arranged in a tabular column.

  The first field is considered the header. A "tabular" column has the property
  that there are no words between the header and any entry in the column.

  The header may be off-aligned with the rest of the fields. The remainder of
  the fields will be pairwise center-, right-, or left-aligned.
  """
  return Conjunction(tuple(chain(
    (all_hold(
      is_tabular_header,
      heads_tabular_entry,
      no_words_between_vertically,
      # FIXME: Magic numbers.
      are_aligned(
        AlignmentLine.VERTICAL_MIDLINES,
        tolerance=0.5,
        taper=10))
      (fields[0], F) for F in fields[1:]),
    ((column(*fields[1:]),) if len(fields) > 2 else tuple()),
  )))
