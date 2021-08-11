"""Rules describing spatial relationships and positioning."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from .textual import count_score

from ..document import Document
from ..entity import Entity
from ..extraction import Field
from ..geometry import BBox, Interval
from ..bp_logging import bp_logging
from ..document import DocRegion, get_pages
from ..functional import pairs
from ..rule import Atom, AtomScore, Degree1Predicate, Degree2Predicate, DegreeError, Lenience, Predicate, Rule, RuleScore, build_conjunction
from ..spatial_formula import Conjunction as LogicalConjunction, DocRegionTerm, Formula, Intersect, IsContained, simplify


def _taper_error(raw_error: float, tolerance: float, taper: float) -> float:
  assert raw_error >= 0.0
  assert tolerance >= 0.0
  assert taper >= 0.0
  error = max(0.0, raw_error - tolerance)
  if error == 0.0:
    return 1.0
  if taper == 0.0:
    return 0.0
  # abs to avoid -0.0 in output.
  return abs(1.0 - min(1.0, error / taper))


def _length_in_native_units(length_from_schema: float, doc: Document) -> float:
  return length_from_schema * doc.median_line_height()


class Direction(str, Enum):
  """A direction."""

  TOP_DOWN = 'TOP_DOWN'
  LEFT_TO_RIGHT = 'LEFT_TO_RIGHT'
  BOTTOM_UP = 'BOTTOM_UP'
  RIGHT_TO_LEFT = 'RIGHT_TO_LEFT'

  def reverse(self) -> 'Direction':
    if self == Direction.LEFT_TO_RIGHT:
      return Direction.RIGHT_TO_LEFT
    if self == Direction.RIGHT_TO_LEFT:
      return Direction.LEFT_TO_RIGHT
    if self == Direction.TOP_DOWN:
      return Direction.BOTTOM_UP
    if self == Direction.BOTTOM_UP:
      return Direction.TOP_DOWN
    assert False


class Orientation(str, Enum):
  """An orientation."""

  HORIZONTAL = 'HORIZONTAL'
  VERTICAL = 'VERTICAL'


class AlignmentLine(str, Enum):
  """An alignment line.

  This is used, for example, as an argument in rules specifying that fields'
  sides or midlines are aligned.
  """

  LEFT_SIDES = 'LEFT_SIDES'
  BOTTOMS = 'BOTTOMS'
  HORIZONTAL_MIDLINES = 'HORIZONTAL_MIDLINES'
  RIGHT_SIDES = 'RIGHT_SIDES'
  TOPS = 'TOPS'
  VERTICAL_MIDLINES = 'VERTICAL_MIDLINES'


@dataclass(frozen=True)
class AreAligned(Degree2Predicate):
  """Says two fields are spatially lined up.

  For multipage documents, the document pages will be assumed to be left-aligned
  when comparing alignment across pages.

  Args:
    anchors: What to check the alignment of. Should be one of the values of the
      AlignmentLine enumeration.
    tolerance: Tolerance band within which the score is 1. Must be set. Note
      that if you set this to 0, you probably want to set a positive taper,
      otherwise the only pairs of fields that will have positive score will be
      ones that are *exactly* aligned.
    taper: Width of the taper-to-0 distance on either side of the tolerance
      band. Defaults to the tolerance.
  """

  anchors: AlignmentLine
  tolerance: float
  taper: float

  def __init__(
    self,
    anchors: AlignmentLine,
    tolerance: float,
    taper: float = None,
    name: str = 'are_aligned',
    uuid: Optional[str] = None,
  ):
    if not isinstance(anchors, AlignmentLine):
      raise ValueError(f'invalid anchors {anchors}')
    if tolerance is None or tolerance < 0:
      raise ValueError(f'tolerance must be nonnegative; got {tolerance}')
    if taper is None:
      taper = tolerance
    if taper < 0:
      raise ValueError(f'taper must be nonnegative; got {taper}')

    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'anchors', anchors)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  def leniency(self) -> float:
      return float(Lenience.LOW)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> AtomScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities
    B1, B2 = E1.bbox, E2.bbox
    r1 = r2 = None
    if self.anchors == AlignmentLine.LEFT_SIDES:
      r1, r2 = B1.ix.a, B2.ix.a
    elif self.anchors == AlignmentLine.RIGHT_SIDES:
      r1, r2 = B1.ix.b, B2.ix.b
    elif self.anchors == AlignmentLine.BOTTOMS:
      r1, r2 = B1.iy.b, B2.iy.b
    elif self.anchors == AlignmentLine.TOPS:
      r1, r2 = B1.iy.a, B2.iy.a
    elif self.anchors == AlignmentLine.HORIZONTAL_MIDLINES:
      r1, r2 = B1.iy.center, B2.iy.center
    elif self.anchors == AlignmentLine.VERTICAL_MIDLINES:
      r1, r2 = B1.ix.center, B2.ix.center

    assert r1 is not None and r2 is not None and self.taper is not None

    score = _taper_error(abs(r1 - r2),
        _length_in_native_units(self.tolerance, doc),
        _length_in_native_units(self.taper, doc))

    return AtomScore(score)

  def _band(self, D: DocRegion) -> DocRegion:
    assert self.taper is not None
    radius = _length_in_native_units(self.tolerance + self.taper, D.document)
    if self.anchors in {AlignmentLine.LEFT_SIDES, AlignmentLine.RIGHT_SIDES,
                    AlignmentLine.VERTICAL_MIDLINES}:
      if self.anchors == AlignmentLine.LEFT_SIDES:
        x0 = D.bbox.ix.a
      elif self.anchors == AlignmentLine.RIGHT_SIDES:
        x0 = D.bbox.ix.b
      else:
        assert self.anchors == AlignmentLine.VERTICAL_MIDLINES
        x0 = D.bbox.ix.center
      return DocRegion(
          D.document, BBox(
            Interval(x0 - radius, x0 + radius), D.document.bbox.iy))
    else:
      assert self.anchors in {
          AlignmentLine.BOTTOMS, AlignmentLine.TOPS,
          AlignmentLine.HORIZONTAL_MIDLINES
      }
      if self.anchors == AlignmentLine.TOPS:
        y0 = D.bbox.iy.a
      elif self.anchors == AlignmentLine.BOTTOMS:
        y0 = D.bbox.iy.b
      else:
        assert self.anchors == AlignmentLine.HORIZONTAL_MIDLINES
        y0 = D.bbox.iy.center
      return DocRegion(
          D.document, BBox(
            D.document.bbox.ix, Interval(y0 - radius, y0 + radius)))

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    if len(fields) != 2:
      raise DegreeError(f'wrong number of fields passed to {self}.phi')
    F1, F2 = fields
    band = lambda D: self._band(D)
    return LogicalConjunction([
      Intersect([DocRegionTerm(F1, band), DocRegionTerm(F2)]),
      Intersect([DocRegionTerm(F2, band), DocRegionTerm(F1)])])


def are_aligned(
  anchors: AlignmentLine,
  tolerance: float,
  taper: Optional[float] = None) \
    -> AreAligned:
  return AreAligned(anchors, tolerance, taper)


@dataclass(frozen=True)
class AreArranged(Degree2Predicate):
  """Says two fields are arranged spatially in some way.

  This rule allows you to specify that one field is to the left or right of
  another, or above or below it, with optional minimum and maximum distances.

  For example: suppose we say that E1, E2 are arranged "left to right". Let x1
  be the x-coordinate of the right side of E1 and let x2 be the x-coordinate of
  the left side of E2. Let d = x2 - x1. This rule scores 1 if d is in the closed
  interval [min_distance, max_distance], and tapers to 0 over the given taper
  distance once d leaves this interval.

  For multipage documents, the document pages will be assumed to be left-aligned
  when comparing arrangement across pages.

  Args:
    direction: Should be a value from the Direction enumeration.
    taper: The score tapers from 0 to 1 as the measured error goes from 0 to
      whatever this number is. Required. It is not recommended to set this to 0.
      Allow some play.
    min_distance: The minimum distance between the fields. Defaults to 0.
    max_distance: The maximum distance between the fields. Defaults to None.
  """

  direction: Direction
  taper: float
  min_distance: float
  max_distance: Optional[float]

  def __init__(
    self,
    direction: Direction,
    taper: float,
    min_distance: float = 0,
    max_distance: Optional[float] = None,
    name: str = 'are_arranged',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'direction', direction)
    object.__setattr__(self, 'taper', taper)
    object.__setattr__(self, 'min_distance', min_distance)
    object.__setattr__(self, 'max_distance', max_distance)

  def leniency(self) -> float:
      return float(Lenience.HIGH)

  def _score_interval_precedence(
      self, i1: Interval, i2: Interval, document: Document) -> float:
    min_i2_a = i1.b + _length_in_native_units(
      self.min_distance or 0, document)
    left_side_error = max(0, min_i2_a - i2.a)

    if self.max_distance is not None:
      max_i2_a = i1.b + _length_in_native_units(self.max_distance, document)
      right_side_error = max(0, i2.a - max_i2_a)
    else:
      right_side_error = 0

    return _taper_error(
        max(left_side_error, right_side_error), 0,
        _length_in_native_units(self.taper, document))

  # Given an interval I, if we wish for another interval I' to be to the right
  # of I, at the same min_distance, max_distance, and taper, what interval must
  # I' be contained in, and what interval must I' intersect? The `reverse`
  # parameter does the same thing supposing that we wish for I' to be to the
  # *left* of I.

  def _containment_interval(self, I: Interval, bounds: Interval,
                            document: Document, reverse: bool = False) \
                            -> Optional[Interval]:
    if reverse:
      return Interval.build(
        bounds.a,
        I.a - _length_in_native_units(
          self.min_distance - self.taper, document))
    else:
      return Interval.build(
        I.b + _length_in_native_units(
          self.min_distance - self.taper, document),
        bounds.b)

  def _intersection_interval(self, I: Interval, bounds: Interval,
                            document: Document, reverse: bool = False) \
                            -> Optional[Interval]:
    if self.max_distance is None:
      return None

    if reverse:
      return Interval.build(
        I.a - _length_in_native_units(
          self.max_distance + self.taper, document),
        bounds.b)
    else:
      return Interval.build(
        bounds.a,
        I.b + _length_in_native_units(
          self.max_distance + self.taper, document))

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities
    B1, B2 = E1.bbox, E2.bbox
    if   self.direction == Direction.LEFT_TO_RIGHT:
      i1, i2 = B1.ix, B2.ix
    elif self.direction == Direction.RIGHT_TO_LEFT:
      i1, i2 = B2.ix, B1.ix
    elif self.direction == Direction.TOP_DOWN:
      i1, i2 = B1.iy, B2.iy
    elif self.direction == Direction.BOTTOM_UP:
      i1, i2 = B2.iy, B1.iy
    assert i1 and i2

    return AtomScore(self._score_interval_precedence(i1, i2, doc))

  # Given a document region D, if we wish for another document region D' to be
  # in the given direction relative to D, at the same min_distance,
  # max_distance, and taper, what document region must D' be contained in, and
  # what document region must D' intersect?

  def _containment_band(self, D: DocRegion, direction: Direction) \
      -> Optional[DocRegion]:
    if direction == Direction.LEFT_TO_RIGHT:
      return DocRegion.build(D.document, BBox.build(
        self._containment_interval(
          D.bbox.ix, D.document.bbox.ix, D.document),
        D.document.bbox.iy))
    if direction == Direction.RIGHT_TO_LEFT:
      return DocRegion.build(D.document, BBox.build(
        self._containment_interval(
          D.bbox.ix, D.document.bbox.ix, D.document, reverse=True),
        D.document.bbox.iy))
    if direction == Direction.TOP_DOWN:
      return DocRegion.build(D.document, BBox.build(
        D.document.bbox.ix,
        self._containment_interval(
          D.bbox.iy, D.document.bbox.iy, D.document)))
    if direction == Direction.BOTTOM_UP:
      return DocRegion.build(D.document, BBox.build(
        D.document.bbox.ix,
        self._containment_interval(
          D.bbox.iy, D.document.bbox.iy, D.document, reverse=True)))
    assert False

  def _intersection_band(self, D: DocRegion, direction: Direction) \
      -> Optional[DocRegion]:
    if self.direction == Direction.LEFT_TO_RIGHT:
      return DocRegion.build(D.document, BBox.build(
        self._intersection_interval(
          D.bbox.ix, D.document.bbox.ix, D.document),
        D.document.bbox.iy))
    if self.direction == Direction.RIGHT_TO_LEFT:
      return DocRegion.build(D.document, BBox.build(
        self._intersection_interval(
          D.bbox.ix, D.document.bbox.ix, D.document, reverse=True),
        D.document.bbox.iy))
    if self.direction == Direction.TOP_DOWN:
      return DocRegion.build(D.document, BBox.build(
        D.document.bbox.ix,
        self._intersection_interval(
          D.bbox.iy, D.document.bbox.iy, D.document)))
    if self.direction == Direction.BOTTOM_UP:
      return DocRegion.build(D.document, BBox.build(
        D.document.bbox.ix,
        self._intersection_interval(
          D.bbox.iy, D.document.bbox.iy, D.document, reverse=True)))
    assert False

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    if len(fields) != 2:
      raise DegreeError(f'wrong number of fields passed to {self}.phi')
    I1, I2 = fields
    min_distance_formula = LogicalConjunction([
      IsContained(
        DocRegionTerm(I2),
        DocRegionTerm(
          I1,
          transformation=lambda I1_D: self._containment_band(
            I1_D, self.direction))),
      IsContained(
        DocRegionTerm(I1),
        DocRegionTerm(
          I2,
          transformation=lambda I2_D: self._containment_band(
            I2_D, self.direction.reverse())))])

    if self.max_distance is not None:
      max_distance_formula: Formula = LogicalConjunction([
        Intersect([
          DocRegionTerm(I2),
          DocRegionTerm(
            I1,
            transformation=lambda I1_D: self._intersection_band(
              I1_D, self.direction))]),
        Intersect([
          DocRegionTerm(I1),
          DocRegionTerm(
            I2,
            transformation=lambda I2_D: self._intersection_band(
              I2_D, self.direction.reverse()))])])
    else:
      max_distance_formula = True

    return simplify(LogicalConjunction([min_distance_formula, max_distance_formula]))


def are_arranged(
    direction: Direction,
    taper: float = 1,
    min_distance: float = 0,
    max_distance: Optional[float] = None) -> AreArranged:
  return AreArranged(direction, taper, min_distance, max_distance)


@dataclass(frozen=True)
class IsInRegion(Degree1Predicate):
  """Says that a field is in a particular region of a document.

  You should usually prefer to use anchoring rules, except in situations where
  something is reliably in a certain part of a document.

  The score function measures the portion of the field's bounding box contained
  in the specified document region.

  The input units are percentage of document width/height.

  If you want to specify the field's position on the specific page that it is
  on, set limit_to_page to True.

  For example:
    Here, the score will be the portion of the field's bounding box contained
    between the vertical lines 10% and 70% from the left of the document:

      is_in_doc_region(x_range=[0.1, 0.7], y_range=None)

    Here, the score will be the portion of the field's bounding box contained
    in the region obtained by intersecting the right half of the document with
    the top quarter:

      is_in_doc_region(x_range=[0.5, 1.0], y_range=[0, 0.25])
  """

  x_range: Optional[Tuple[float, float]]
  y_range: Optional[Tuple[float, float]]
  limit_to_page: bool

  def __init__(
    self,
    x_range: Optional[Tuple[float, float]],
    y_range: Optional[Tuple[float, float]],
    limit_to_page: bool,
    name: str = 'is_in_region',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'x_range', x_range)
    object.__setattr__(self, 'y_range', y_range)
    object.__setattr__(self, 'limit_to_page', limit_to_page)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]

    assert self.x_range is None or len(self.x_range) == 2
    assert self.y_range is None or len(self.y_range) == 2

    if self.limit_to_page:
      entity_pages = get_pages(E, doc)
      assert len(entity_pages) > 0
      if len(entity_pages) > 1:
        # FIXME: Check the regions on both pages, not just the first page.
        bp_logging.warning(f'entity {E} spans multiple pages, using first page '
                          'for IsInDocRegion')
      doc_bbox = entity_pages[0].bbox
    else:
      doc_bbox = doc.bbox

    # FIXME: This ignores the rotation/orientation of the documents.
    doc_ix = doc_bbox.ix
    doc_iy = doc_bbox.iy
    x_legal_range = Interval(
      doc_ix.a + self.x_range[0] * doc_ix.length,
      doc_ix.b - (1 - self.x_range[1]) * doc_ix.length) \
        if self.x_range else None
    y_legal_range = Interval(
      doc_iy.a + self.y_range[0] * doc_iy.length,
      doc_iy.b - (1 - self.y_range[1]) * doc_iy.length) \
        if self.y_range else None

    x_percentage = x_legal_range.contains_percentage_of(
      E.bbox.ix) if x_legal_range else 1
    y_percentage = y_legal_range.contains_percentage_of(
      E.bbox.iy) if y_legal_range else 1

    return AtomScore(x_percentage * y_percentage)


@dataclass(frozen=True)
class PageNumberIs(Degree1Predicate):
  """Says a field is on one of the given pages.

  The first page of the document is considered to be page 1.

  Args:
    score_dict: A map from page number to score. For page numbers above the
      largest or below the smallest map key, we use the scores corresponding to
      the largest and smallest map keys, respectively. We linearly interpolate
      to compute scores for absent intermediate page numbers. See example.

  In the following example code, the resulting score, depending on the
  assignment for the field, will be:
    * 0 for assignments on page 1 or 5,
    * 0.5 for assignments on page 2,
    * 0.75 for assignments on page 3 (due to lerping),
    * 1 for assignments on page 4, and
    * 0.3 for assignments on page 6 or later.

  Example code:
    page_number_is(score_dict={
      1: 0,
      2: 0.5,
      4: 1,
      5: 0,
      6: 0.3,
    })('shipping_address')
  """

  score_dict: Dict

  def __init__(
    self,
    score_dict: Dict,
    name: str = 'page_number_is',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'score_dict', score_dict)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]

    return AtomScore(max(count_score(self.score_dict, page.page_number)
      for page in get_pages(E, doc)))

  def __hash__(self) -> int:
    return id(self)

  def __eq__(self, other: Any) -> bool:
    if type(self) != type(other):
      return False
    return hash(self) == hash(other)


@dataclass(frozen=True)
class AreOnSamePage(Degree2Predicate):
  """Says that two fields are on the same page of the document.

  The page error is the number of pages of separation between two fields.

  Args:
    tolerance: Will score 1 if the page error is at most this amount. Must be a
      nonnegative integer.
    taper: The score tapers from 1 to 0 as the page error minus the tolerance
      goes from 0 to taper+1 inclusive. Must be a nonnegative integer.

  In the following example code, the resulting score, depending on the
  assignments for fields F1 and F2, will be:

    * 1   for F1 on page 2, F2 on page 2
    * 0.5 for F1 on page 1, F2 on page 2
    * 0   for F1, F2 separated by more than 1 page

  Example code:
    are_on_same_page(tolerance=0, taper=1)
  """

  def __init__(
    self,
    tolerance: int,
    taper: int,
    name: str = 'are_on_same_page',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)

  tolerance: int
  taper: int

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities
    E1_page_numbers: Tuple[int, ...] = tuple(P.page_number
      for P in get_pages(E1, doc))
    E2_page_numbers: Tuple[int, ...] = tuple(P.page_number
      for P in get_pages(E2, doc))
    error = min(E1_page_numbers) - max(E2_page_numbers) \
      if min(E1_page_numbers) >= max(E2_page_numbers) \
      else min(E2_page_numbers) - max(E1_page_numbers)
    score = _taper_error(error, self.tolerance, self.taper+1)
    return AtomScore(score)


@dataclass(frozen=True)
class BottomAligned(AreAligned):

  def __init__(
    self,
    tolerance: float = 0.5,
    taper: float = 0.5,
    name: str = 'bottom_aligned',
    uuid: Optional[str] = None,
    anchors: AlignmentLine = AlignmentLine.BOTTOMS,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
      tolerance = tolerance,
      taper = taper,
      anchors = anchors,
    )


@dataclass(frozen=True)
class LeftAligned(AreAligned):

  def __init__(
    self,
    tolerance: float = 1,
    taper: float = 1,
    name: str = 'left_aligned',
    uuid: Optional[str] = None,
    anchors: AlignmentLine = AlignmentLine.LEFT_SIDES,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
      tolerance = tolerance,
      taper = taper,
      anchors = AlignmentLine.LEFT_SIDES,
    )


@dataclass(frozen=True)
class RightAligned(AreAligned):

  def __init__(
    self,
    tolerance: float = 1,
    taper: float = 1,
    name: str = 'right_aligned',
    uuid: Optional[str] = None,
    anchors: AlignmentLine = AlignmentLine.RIGHT_SIDES,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
      tolerance = tolerance,
      taper = taper,
      anchors = anchors,
    )


@dataclass(frozen=True)
class LeftToRight(AreArranged):

  def __init__(
    self,
    taper: float = 0.5,
    min_distance: float = 0,
    max_distance: Optional[float] = None,
    name: str = 'left_to_right',
    uuid: Optional[str] = None,
    direction: Direction = Direction.LEFT_TO_RIGHT,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
      taper = taper,
      min_distance = min_distance,
      max_distance = max_distance,
      direction = direction,
    )


@dataclass(frozen=True)
class TopDown(AreArranged):

  def __init__(
    self,
    taper: float = 0.5,
    min_distance: float = 0,
    max_distance: Optional[float] = None,
    name: str = 'top_down',
    uuid: Optional[str] = None,
    direction: Direction = Direction.TOP_DOWN,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
      taper = taper,
      min_distance = min_distance,
      max_distance = max_distance,
      direction = direction,
    )


def left_aligned(*fields: Field) -> Rule:
  return build_conjunction(fields, LeftAligned)


def bottom_aligned(*fields: Field) -> Rule:
  return build_conjunction(fields, BottomAligned)


def right_aligned(*fields: Field) -> Rule:
  return build_conjunction(fields, RightAligned)


def top_down(*fields: Field) -> Rule:
  return build_conjunction(fields, TopDown)


def left_to_right(*fields: Field) -> Rule:
  return build_conjunction(fields, LeftToRight)


left_to_right_pair = LeftToRight
top_down_pair = TopDown
bottom_aligned_pair = BottomAligned
left_aligned_pair = LeftAligned
right_aligned_pair = RightAligned


def is_in_doc_region(
    x_range: Optional[Tuple[float, float]],
    y_range: Optional[Tuple[float, float]]) -> Predicate:
  return IsInRegion(x_range, y_range, limit_to_page=False)


def is_in_page_region(
    x_range: Optional[Tuple[float, float]] = None,
    y_range: Optional[Tuple[float, float]] = None) -> Predicate:
  return IsInRegion(x_range, y_range, limit_to_page=True)


"""
  Says that the first field is one line above the second.

  "One line above" means that the second field is on the next logical line
  following the first, not that there is a full line of space separating them.

  Example code:
    extract(
      column(['label', 'value'])
      one_line_above('label', 'value'))
"""
one_line_above = are_arranged(Direction.TOP_DOWN, max_distance=0.5, taper=0.5)


"""
  Says that the first of two fields is one-to-two lines above the second.

  Similar to `one_line_above`.
"""
one_to_two_lines_above = are_arranged(Direction.TOP_DOWN, max_distance=1.5, taper=0.5)
