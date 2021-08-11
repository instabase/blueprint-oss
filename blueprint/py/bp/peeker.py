import heapq

from typing import Dict, Generic, Iterator, List, Optional, TypeVar

T = TypeVar('T')


class Peeker(Iterator[T]):
  """Forward the values of a sequence, constantly peeking a specified distance
  ahead and preferring to return smaller values first."""

  def __init__(self, ts: Iterator[T], peek_distance: int = 1):
    """Configure the peeker.

    Args:
      ts: An iterator of Ts.
      peek_distance: The Peeker will maintain a (min-)heap of this many elements
        from ts. When __next__ is called, we retrieve another element from ts,
        add it to the heap, and then pop/return the top of the heap.
    """
    if peek_distance < 0:
      raise ValueError(f'peek_distance must be nonnegative, not {peek_distance}')

    self.ts = ts
    self.peek_distance = peek_distance
    self.heap: Optional[List[T]] = None

  def __next__(self) -> T:
    if self.heap is None:
      self.initialize()
    assert self.heap is not None

    self._step()

    if self.heap == []:
      raise StopIteration

    return heapq.heappop(self.heap)

  def initialize(self) -> None:
    if self.heap is not None:
      raise RuntimeError('attempted initialization multiple times')

    self.heap = []
    for _ in range(self.peek_distance):
      self._step()

  def _step(self) -> None:
    assert self.heap is not None
    try:
      heapq.heappush(self.heap, next(self.ts))
    except StopIteration:
      pass

  @property
  def top(self) -> Optional[T]:
    """The top of the heap.

    If peek_distance is 0, this will always be None.

    It is *not* guaranteed that `next(peeker)` will return `peeker.top`.
    """
    return self.heap[0] if self.heap else None
