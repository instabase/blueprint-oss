"""Rules for describing impingement.

Impingement is when something obstructs a region or a clear line of sight
between two points. For example, suppose we have two entities that we think are
a label/value pair. We may ask that the space between them be unimpinged,
meaning that there are no other entities occupying that space. If the space is
impinged upon, then maybe it's unlikely that the entities we've chosen for the
label/value pair are correct.
"""

from dataclasses import dataclass
from itertools import chain
from mypy_extensions import VarArg
from typing import Callable, Optional, Tuple
from uuid import uuid4

from ..bp_logging import bp_logging
from ..document import DocRegion, Document, build_words_ez_doc_region, get_pages
from ..entity import Entity, Page
from ..functional import pairs
from ..geometry import BBox, Interval
from ..impingement import Impingement
from ..rule import AtomScore, DegreeError, Lenience, Predicate, RuleScore
from ..rules.spatial import Orientation


IMPINGEMENT_SMALL_INSET = 0.25
IMPINGEMENT_LARGE_INSET = 1.0


@dataclass(frozen=True)
class BoxUnimpinged(Predicate):
  """Says that a particular document region is not impinged upon.

  If we say that a box is unimpinged in the horizontal direction, this means
  that if we are standing on the left side of the box, we can see clear through
  to the right side -- there is nothing in the way, impinging our view.
  Impingement in the vertical direction is defined analogously.
  For multipage documents, the document pages will be assumed to be left-aligned
  when measuring impingement across pages.

  Args:
    doc_region_getter: Defines the document region which should be unimpinged in
      terms of a document and some number of entities.
    direction: The direction in which we are measuring impingement. Should be
      one of the values of the Orientation enumeration.
    degree_: The number of entities that doc_region_getter takes as argument.
      This should be a positive integer.
    illegal_characters: Normally, all impinging text is counted. If this is set,
      only these characters will be considered "illegal".
    maximum_impingement: If the total impingement (a number between 0 and 1) is
      above this number, will return a score of 0.
  """

  def __init__(
    self,
    direction: Orientation,
    degree_: int = 2,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 1.0,
    name: str = 'box_unimpinged',
    uuid: Optional[str] = None,
  ):
    if degree_ < 1:
      raise DegreeError(f'box_unimpinged degree must be at least 1, not {degree_}')

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
    )
    object.__setattr__(self, 'direction', direction)
    object.__setattr__(self, 'degree_', degree_)
    object.__setattr__(self, 'illegal_characters', illegal_characters)
    object.__setattr__(self, 'maximum_impingement', maximum_impingement)

  direction: Orientation
  degree_: int
  illegal_characters: Optional[str]
  maximum_impingement: float

  def leniency(self) -> float:
      return float(Lenience.LOW)

  @property
  def degree(self) -> int:
    return self.degree_

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    raise NotImplementedError

  def get_opacity(self, text: Optional[str]) -> float:
    if text is None or len(text) == 0:
      return 0.0
    if self.illegal_characters is None:
      return 1.0
    return sum(1 for c in text if c in self.illegal_characters) / len(text)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:

    doc_region = self.doc_region_getter(doc, *entities)

    # An empty or invalid box is considered to be unimpinged.
    if doc_region is None or not doc_region.bbox.non_empty:
      return AtomScore(1)

    def projection(doc_region: DocRegion) -> Interval:
      if self.direction == Orientation.VERTICAL:
        return doc_region.bbox.ix
      else:
        assert self.direction == Orientation.HORIZONTAL
        return doc_region.bbox.iy

    impingement_interval = Impingement(projection(doc_region))
    box_defining_words = frozenset(
        chain.from_iterable(entity.entity_words() for entity in entities))

    words_ez_doc_region = build_words_ez_doc_region(doc)
    for E in words_ez_doc_region.ts_intersecting(doc_region):
      assert len(tuple(E.entity_words())) == 1
      if tuple(E.entity_words())[0] not in box_defining_words:
        E_doc_region = DocRegion.build(doc, E.bbox)
        assert E_doc_region
        impingement_interval.incorporate_subdivision(
          projection(E_doc_region), self.get_opacity(E.entity_text))

    if impingement_interval.total_impingement > self.maximum_impingement:
      return AtomScore(0)

    return AtomScore(1 - impingement_interval.total_impingement)


def _erode_if_possible(interval: Interval, amount: float) -> Interval:
  eroded_interval = interval.eroded(amount)
  if eroded_interval is None:
    return interval
  return eroded_interval


def _space_between_vertically(E1: Entity, E2: Entity, doc: Document,
                              spanning: bool) -> Optional[DocRegion]:
  """The vertical space between two entities."""
  if spanning:
    ix = Interval.spanning_intervals([E1.bbox.ix, E2.bbox.ix])
  else:
    intersection = Interval.intersection([E1.bbox.ix, E2.bbox.ix])
    if intersection is None:
      return None
    ix = intersection
  return DocRegion.build(doc, BBox.build(
    _erode_if_possible(ix, IMPINGEMENT_SMALL_INSET * doc.median_line_height()),
    _erode_if_possible(
      Interval(E1.bbox.iy.b, E2.bbox.iy.a),
      IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


def _space_between_horizontally(E1: Entity, E2: Entity, doc: Document,
                                spanning: bool) -> Optional[DocRegion]:
  """The horizontal space between two entities."""
  if spanning:
    iy = Interval.spanning_intervals([E1.bbox.iy, E2.bbox.iy])
  else:
    intersection = Interval.intersection([E1.bbox.iy, E2.bbox.iy])
    if intersection is None:
      return None
    iy = intersection
  return DocRegion.build(doc, BBox.build(
    _erode_if_possible(
      Interval(E1.bbox.ix.b, E2.bbox.ix.a),
      IMPINGEMENT_SMALL_INSET * doc.median_line_height()),
    _erode_if_possible(iy, IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


def get_page_for_edge(E: Entity, doc: Document) -> Page:
  entity_pages = get_pages(E, doc)
  assert len(entity_pages) > 0
  if len(entity_pages) > 1:
    # FIXME: Check the impingement on both pages, not just the first page.
    bp_logging.warning(f'entity {E} spans multiple pages, using first page '
                        'for page edge impingement rules')
  return entity_pages[0]


# FIXME: When we support multiline clustering across pages, these edge rules
# will need to be updated.
def _space_between_top_edge(doc: Document, E: Entity) -> Optional[DocRegion]:
  """The vertical space between an entity and the top edge of the page."""
  page = get_page_for_edge(E, doc)
  return DocRegion.build(doc, BBox.build(E.bbox.ix,
    Interval(page.bbox.iy.a, E.bbox.iy.a)))


def _space_between_bottom_edge(doc: Document, E: Entity) -> Optional[DocRegion]:
  """The vertical space between an entity and the bottom edge of the page."""
  page = get_page_for_edge(E, doc)
  return DocRegion.build(doc, BBox.build(E.bbox.ix,
    Interval(E.bbox.iy.b, page.bbox.iy.b)))


def _space_between_left_edge(doc: Document, E: Entity) -> Optional[DocRegion]:
  """The horizontal space between an entity and the left edge of the page."""
  page = get_page_for_edge(E, doc)
  return DocRegion.build(doc, BBox.build(
    Interval(page.bbox.ix.a, E.bbox.ix.a),
    _erode_if_possible(
      E.bbox.iy, IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


def _space_between_right_edge(doc: Document, E: Entity) -> Optional[DocRegion]:
  """The horizontal space between an entity and the right edge of the page."""
  page = get_page_for_edge(E, doc)
  return DocRegion.build(doc, BBox.build(
    Interval(E.bbox.ix.b, page.bbox.width),
    _erode_if_possible(
      E.bbox.iy,
      IMPINGEMENT_SMALL_INSET * doc.median_line_height())))


@dataclass(frozen=True)
class NothingBetweenHorizontally(BoxUnimpinged):

  spanning: bool

  def __init__(
    self,
    name: str = 'nothing_between_horizontally',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.HORIZONTAL,
    degree_: int = 2,
    spanning: bool = False,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 1.0,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )
    object.__setattr__(self, 'spanning', spanning)

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _space_between_horizontally(E1, E2, doc, self.spanning)


@dataclass(frozen=True)
class NothingBetweenVertically(BoxUnimpinged):

  spanning: bool

  def __init__(
    self,
    name: str = 'nothing_between_vertically',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.VERTICAL,
    degree_: int = 2,
    spanning: bool = False,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 1.0,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )
    object.__setattr__(self, 'spanning', spanning)

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _space_between_vertically(E1, E2, doc, self.spanning)


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class NoWordsBetweenVertically(BoxUnimpinged):

  spanning: bool

  """Says that there are no words in the vertical space between two entities.

  Example:
    This can be useful in the context of a table, where a column has several
    numeric values under its heading. So something like this would be ok:

        Amounts <- label we are looking for
         $50.00
         $25.00
         $30.00 <- value we are looking for
  """
  def __init__(
    self,
    name: str = 'no_words_between_vertically',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.VERTICAL,
    degree_: int = 2,
    spanning: bool = False,
    illegal_characters: str = LETTERS,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )
    object.__setattr__(self, 'spanning', spanning)

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _space_between_vertically(E1, E2, doc, self.spanning)


@dataclass(frozen=True)
class NoWordsBetweenHorizontally(BoxUnimpinged):

  spanning: bool

  """Says that there are no words in the horizontal space between two entities.

  Similar to `NoWordsBetweenVertically`.
  """
  def __init__(
    self,
    name: str = 'no_words_between_horizontally',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.HORIZONTAL,
    degree_: int = 2,
    spanning: bool = False,
    illegal_characters: str = LETTERS,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )
    object.__setattr__(self, 'spanning', spanning)

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 2
    E1, E2 = Es
    return _space_between_horizontally(E1, E2, doc, self.spanning)


def nothing_between_vertically_custom(
    spanning: bool = False,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 1.0,) -> Predicate:
  return NothingBetweenVertically(
    'nothing_between_vertically', None, Orientation.VERTICAL, 2,
    spanning, illegal_characters, maximum_impingement)


def nothing_between_horizontally_custom(
    spanning: bool = False,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 1.0,) -> Predicate:
  return NothingBetweenHorizontally(
    'nothing_between_horizontally', None, Orientation.HORIZONTAL, 2,
    spanning, illegal_characters, maximum_impingement)


def no_words_between_vertically_custom(
    spanning: bool = False,
    illegal_characters: str = LETTERS,
    maximum_impingement: float = 0.5,) -> Predicate:
  return NoWordsBetweenVertically(
    'no_words_between_vertically', None, Orientation.VERTICAL, 2,
    spanning, illegal_characters, maximum_impingement)


def no_words_between_horizontally_custom(
    spanning: bool = False,
    illegal_characters: str = LETTERS,
    maximum_impingement: float = 0.5,) -> Predicate:
  return NoWordsBetweenHorizontally(
    'no_words_between_horizontally', None, Orientation.HORIZONTAL, 2,
    spanning, illegal_characters, maximum_impingement)


class NothingBetweenLeftEdge(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'nothing_between_left_edge',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.HORIZONTAL,
    degree_: int = 1,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    return _space_between_left_edge(doc, *Es)


class NothingBetweenRightEdge(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'nothing_between_right_edge',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.HORIZONTAL,
    degree_: int = 1,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    return _space_between_right_edge(doc, *Es)


class NothingBetweenTopEdge(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'nothing_between_top_edge',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.VERTICAL,
    degree_: int = 1,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    return _space_between_top_edge(doc, *Es)


class NothingBetweenBottomEdge(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'nothing_between_bottom_edge',
    uuid: Optional[str] = None,
    direction: Orientation = Orientation.VERTICAL,
    degree_: int = 1,
    illegal_characters: Optional[str] = None,
    maximum_impingement: float = 0.5,
  ):

    super().__init__(
      uuid = str(uuid4()) if uuid is None else uuid,
      name = name,
      direction = direction,
      degree_ = degree_,
      illegal_characters = illegal_characters,
      maximum_impingement = maximum_impingement,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    return _space_between_bottom_edge(doc, *Es)


nothing_between_vertically = nothing_between_vertically_custom()
nothing_between_horizontally = nothing_between_horizontally_custom()
no_words_between_vertically = no_words_between_vertically_custom()
no_words_between_horizontally = no_words_between_horizontally_custom()


nothing_between_left_edge = NothingBetweenLeftEdge()
nothing_between_right_edge = NothingBetweenRightEdge()
nothing_between_top_edge = NothingBetweenTopEdge()
nothing_between_bottom_edge = NothingBetweenBottomEdge()
