from typing import Dict, Generator, Generic, List, Optional, TypeVar


T = TypeVar('T')


class TrivialPrefilter(Generic[T]):
  """A prefilter that does nothing but hold the elements that pass through it in
  a list, and keep track of the best one.

  Any element of the feeder stream is considered compatible with every element
  of the target stream.
  """

  def __init__(self) -> None:
    self._list: List[T] = []

    # FIXME: It's a bit janky to have this 'top-scoring' logic here.
    self.best: Optional[T] = None

  def add(self, t_target: T) -> None:
    # FIXME: It's a bit janky to have this 'top-scoring' logic here.
    # FIXME: I'm not sure there is an easy way to say, in Python, that T must have a less-than
    # operator on it.
    if self.best is None or t_target < self.best:  # type: ignore
      self.best = t_target

    self._list.append(t_target)

  def get(self, t_feeder: T) -> Generator[T, None, None]:
    yield from self._list
