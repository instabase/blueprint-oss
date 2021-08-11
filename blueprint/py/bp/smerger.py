"""Smergers."""

import dataclasses
import heapq

from itertools import product
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Tuple, TypeVar

from .extraction import Extraction
from .functional import arg_max, arg_min
from .peeker import Peeker
from .scoring import ScoredExtraction
from .trivial_prefilter import TrivialPrefilter


T = TypeVar('T')


@dataclasses.dataclass
class _Stream(Iterator[T]):
  peeker: Peeker
  prefilter: Any
  _initialized: bool = False

  def __next__(self) -> T:
    assert self._initialized
    t = next(self.peeker)
    self.prefilter.add(t)
    return t

  def initialize(self) -> None:
    assert not self._initialized
    self.peeker.initialize()
    self._initialized = True

  @staticmethod
  def build_trivial() -> '_Stream':
    prefilter: TrivialPrefilter = TrivialPrefilter()
    prefilter.add(ScoredExtraction.build())
    stream: _Stream = _Stream(
      Peeker(iter(tuple())), prefilter)
    stream.initialize()
    return stream

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, _Stream):
      return False
    return id(self) == id(other)


class Smerger(Iterator[T]):
  """Combines several roughly-increasing sequences into a single roughly-
  increasing sequence.

  Let x1, x2, ..., and y1, y2, ..., be roughly-increasing sequences, meaning
  that often, but maybe not always, if i < j then xi < xj and yi < yj. Suppose
  we have a way of "adding" the xis and the yjs. (The xs and ys may not be
  numbers.) A *smerger* is an iterator which yields a sequence of sums xi + yj,
  also in roughly-increasing order.

  A smerger makes the guarantee that for every i, j pair, it will eventually
  emit xi + yj, with multiplicity, unless all_or_nothing is True.
  """

  def __init__(
      self,
      streams: Tuple[Tuple[Iterator[T], Any], ...],
      merger: Callable[[Tuple[T, ...]], Optional[T]],
      norm_estimator: Callable[[Tuple[T, ...]], float],
      norm_getter: Callable[[T], float],
      all_or_nothing: bool = False,
      peek_distance: int = 1,
      optimistic: bool = False):
    """Configure the smerger.

    If you are using this for extractions and using their scores for the norm,
    as is typical, keep in mind that you need to *negate* the scores when
    writing the norm functions below, since this data structure returns Ts
    (roughly) from *smallest* to largest.

    Args:
      streams: A collection of N iterators. Conceptually, each of these should
        emit its elements in roughly smallest-to-largest order, although nothing
        technically hinges on this assumption.
      merger: A function which takes N Ts and combines them into a T to be
        emitted by this smerger. The ith input T comes from the ith stream. This
        is allowed to return None to indicate that the merge failed (gracefully)
        and the result was discarded.
      norm_estimator: Given N Ts, again the ith one coming from the ith stream,
        estimate the norm we would get if we were to combine them using merger.
      norm_getter: Given a T, conceptually the result of using merger, return
        its norm.
      peek_distance: Each of the streams will be assigned to a Peeker. This
        configures the Peekers' peek distances.
      optimistic: If this is set to true, then we will step prior to returning a
        __next__ value as long as the Ts we can see at the tops of the
        underlying peekers, if combined, would result in a better norm estimate
        than the norm of the top element of our own heap.
      all_or_nothing: If True, and one stream emits only an empty extraction,
        iteration will terminate early and only an empty extraction will be
        emitted.
    """
    if peek_distance < 1:
      raise ValueError(f'peek_distance must be positive, not {peek_distance}')

    self.optimistic = optimistic
    self.all_or_nothing = all_or_nothing

    self._streams: Tuple[_Stream, ...] = tuple(
        _Stream(Peeker(iterator, peek_distance=peek_distance), prefilter)
        for iterator, prefilter in streams)
    self._merger = merger
    self._norm_estimator = norm_estimator
    self._norm_getter = norm_getter
    self._heap: Optional[List[T]] = None

  def __next__(self) -> T:
    if self._heap is None:
      self.initialize()
    assert self._heap is not None

    if all(stream.prefilter.best is not None for stream in self._streams):
      while self._heap == [] and any(
          stream.peeker.top is not None for stream in self._streams):
        self._step(
            arg_min(
                lambda stream: self._optimistic_norm(stream),
                filter(
                    lambda stream: stream.peeker.top is not None,
                    self._streams)))

      if self.optimistic and self._heap != []:

        def appealing(stream: _Stream) -> bool:
          assert self._heap is not None
          return stream.peeker.top is not None and \
                  self._optimistic_norm(stream) < self._norm_getter(self._heap[0])

        while any(appealing(stream) for stream in self._streams):
          self._step(
              arg_min(
                  lambda stream: self._optimistic_norm(stream),
                  filter(appealing, self._streams)))

    if self._heap == []:
      raise StopIteration

    return heapq.heappop(self._heap)

  def initialize(self) -> None:
    if self._heap is not None:
      raise RuntimeError('attempted initialization multiple times')

    self._heap = []
    for stream in self._streams:
      stream.initialize()

    # Empty extraction is always returned last from a stream.
    only_empty: Callable[[_Stream], bool] = lambda S: \
        S.peeker.top is not None and S.peeker.top.is_empty

    if self.all_or_nothing and any(only_empty(S) for S in self._streams):
      self._streams = tuple(map(lambda S: S if only_empty(S)
          else _Stream.build_trivial(), self._streams))

    for stream in self._streams:
      if stream.peeker.top is not None:  # Some streams may come up empty.
        self._step(stream)

  def _step(self, stepping_stream: _Stream) -> None:
    assert self._heap is not None

    t = next(stepping_stream)

    def ts(stream: _Stream) -> Tuple[T, ...]:
      if stream == stepping_stream:
        return (t,)
      # FIXME: This is broken for non-trivial prefilters for non-binary smergers.
      return tuple(stream.prefilter.get(t))

    for tup in product(*(ts(stream) for stream in self._streams)):
      new_t = self._merger(tup)
      if new_t is not None:
        heapq.heappush(self._heap, new_t)

  def _optimistic_norm(self, stream: _Stream) -> float:
    assert all(
        any_stream.prefilter.best is not None for any_stream in self._streams)
    assert stream.peeker.top is not None

    def contribution(some_stream: _Stream) -> T:
      if some_stream == stream:
        assert stream.peeker.top is not None
        return stream.peeker.top
      assert some_stream.prefilter.best is not None
      return some_stream.prefilter.best

    return self._norm_estimator(tuple(map(contribution, self._streams)))

  def __str__(self) -> str:
    return 'Smerger()'
