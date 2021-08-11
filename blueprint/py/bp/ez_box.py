import itertools

from typing import Callable, Generator, Generic, Optional, Set, Tuple, TypeVar

from .geometry import BBox, Interval

T = TypeVar('T')


class EZBox(Generic[T]):

  def __init__(
      self,
      bbox: BBox,
      bbox_getter: Callable[[T], BBox],
      ideal_width_to_height_ratio: float = 20):
    self.bbox = bbox
    self.bbox_getter = bbox_getter
    self.ideal_width_to_height_ratio = ideal_width_to_height_ratio
    self.straddlers: Set[T] = set()
    self.child_nodes: Tuple['EZBox[T]', ...] = tuple()

  def __str__(self) -> str:
    return 'EZBox({}, {}, {}, {})'.format(
        self.bbox, self.ideal_width_to_height_ratio, self.straddlers,
        self.child_nodes)

  def insert(self, t: T) -> None:
    bbox = self.bbox_getter(t)
    if not self.bbox.contains_bbox(bbox):
      raise ValueError(
          f'attempted to insert out-of-bounds item {t} into {self}')

    if self.child_nodes:
      for child in self.child_nodes:
        if child.bbox.contains_bbox(bbox):
          child.insert(t)
          return
      self.straddlers.add(t)
      return

    self.straddlers.add(t)
    if len(self.straddlers) > 5:  # FIXME: Magic number.
      self._split()

  def ts(self) -> Generator[T, None, None]:
    yield from self.straddlers
    yield from itertools.chain.from_iterable(
        child.ts() for child in self.child_nodes)

  def ts_contained_in(self, bbox_: BBox) -> Generator[T, None, None]:
    bbox = BBox.intersection([bbox_, self.bbox])
    if not bbox:
      return

    for straddler in self.straddlers:
      if bbox.contains_bbox(self.bbox_getter(straddler)):
        yield straddler

    for child in self.child_nodes:
      yield from child.ts_contained_in(bbox)

  def ts_intersecting(self, bbox_: BBox) -> Generator[T, None, None]:
    bbox = BBox.intersection([bbox_, self.bbox])
    if not bbox:
      return

    for straddler in self.straddlers:
      if bbox.intersects_bbox(self.bbox_getter(straddler)):
        yield straddler

    for child in self.child_nodes:
      yield from child.ts_intersecting(bbox)

  def _split(self) -> None:
    assert not self.child_nodes

    ts = self.straddlers
    self.straddlers = set()

    VERTICAL_SPLIT = 1
    HORIZONTAL_SPLIT = 2

    current_ratio = self.bbox.ix.length / self.bbox.iy.length
    v_ratio = 0.5 * current_ratio
    h_ratio = 2 * current_ratio

    # I'm not really sure this is ideal.
    v_error = abs(1 - v_ratio / self.ideal_width_to_height_ratio)
    h_error = abs(1 - h_ratio / self.ideal_width_to_height_ratio)

    CHOICE = VERTICAL_SPLIT if v_error < h_error else HORIZONTAL_SPLIT

    if CHOICE == VERTICAL_SPLIT:
      l, c, r = self.bbox.ix.a, self.bbox.ix.center, self.bbox.ix.b
      left = EZBox(
          BBox(Interval(l, c), self.bbox.iy), self.bbox_getter,
          self.ideal_width_to_height_ratio)
      right = EZBox(
          BBox(Interval(c, r), self.bbox.iy), self.bbox_getter,
          self.ideal_width_to_height_ratio)
      self.child_nodes = (left, right)
    else:
      u, c, l = self.bbox.iy.a, self.bbox.iy.center, self.bbox.iy.b
      upper = EZBox(
          BBox(self.bbox.ix, Interval(u, c)), self.bbox_getter,
          self.ideal_width_to_height_ratio)
      lower = EZBox(
          BBox(self.bbox.ix, Interval(c, l)), self.bbox_getter,
          self.ideal_width_to_height_ratio)
      self.child_nodes = (upper, lower)

    for t in ts:
      self.insert(t)
