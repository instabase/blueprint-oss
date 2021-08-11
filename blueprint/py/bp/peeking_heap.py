import heapq

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple, TypeVar

from .peeker import Peeker


T = TypeVar('T')


class PeekingHeap(Iterator[T]):

  def __init__(
      self,
      tss: Iterable[Iterator[T]],
      normalizer: Callable[[T], T],
      peek_distance: int = 1):
    if peek_distance < 1:
      raise ValueError(f'peek_distance must be positive, not {peek_distance}')

    self._tss = tss
    self._normalizer = normalizer
    self._peek_distance = peek_distance
    self._heap: Optional[List[Tuple[T, int, Peeker[T]]]] = None
    self._counter = 0

  def __next__(self) -> T:
    if self._heap is None:
      self.initialize()
    assert self._heap is not None

    if self._heap == []:
      raise StopIteration

    _, _, peeker = heapq.heappop(self._heap)
    t = self._normalizer(next(peeker))
    assert t is not None
    self._add(peeker)
    return t

  def initialize(self) -> None:
    if self._heap is not None:
      raise RuntimeError('attempted initialization multiple times')

    self._heap = []
    for ts in self._tss:
      peeker = Peeker(ts, self._peek_distance)
      peeker.initialize()
      self._add(peeker)

  def _add(self, peeker: Peeker) -> None:
    assert self._heap is not None
    if peeker.top is not None:
      heapq.heappush(
          self._heap, (self._normalizer(peeker.top), self._counter,
                        peeker))  # Counter breaks tie between top values.
      self._counter += 1

  @property
  def top(self) -> Optional[T]:
    return self._heap[0][0] if self._heap else None
