from itertools import chain, tee
from typing import Callable, Collection, Dict, FrozenSet, Generator, Iterable, Optional, Set, Tuple, TypeVar


T = TypeVar('T')


def arg_max(f: Callable[[T], float], ts: Iterable[T]) -> T:
  ts = tuple(ts)
  if not ts:
    raise ValueError('empty input')
  best = None
  for t in ts:
    candidate = (t, f(t))
    if best is None or candidate[1] > best[1]:
      best = candidate
  assert best
  return best[0]


def arg_min(f: Callable[[T], float], ts: Iterable[T]) -> T:
  if not ts:
    raise ValueError('empty input')
  return arg_max(lambda t: -f(t), ts)


def comma_sep(ts: Iterable[T]) -> str:
  return ', '.join(map(str, ts))


def pairs(ts: Iterable[T]) -> Generator[Tuple[T, T], None, None]:
  ts = tuple(ts)
  for i in range(len(ts)):
    for j in range(i + 1, len(ts)):
      yield (ts[i], ts[j])


def ordered_pairs(ts: Iterable[T]) -> Generator[Tuple[T, T], None, None]:
  ts = tuple(ts)
  for i in ts:
    for j in ts:
      if i != j:
        yield (i, j)


def adjacent_pairs(ts: Iterable[T]) -> Generator[Tuple[T, T], None, None]:
  ts = tuple(ts)
  for i in range(len(ts) - 1):
    yield (ts[i], ts[i+1])


def pairwise_disjoint(tss: Iterable[Iterable[T]]) -> bool:
  s: Set[T] = set()
  for t in chain.from_iterable(tss):
    if t in s:
      return False
    s.add(t)
  return True


def uniq(ts: Iterable[T]) -> Generator[T, None, None]:
  s = set()
  for t in ts:
    if t not in s:
      s.add(t)
      yield t


def all_distinct(ts: Collection[T]) -> bool:
  """Are all of the ts different from one another?"""
  return len(ts) == len(set(ts))


def multiplicities(ts: Collection[T]) -> Dict[T, int]:
  """How often does each t appear in ts?"""
  result: Dict[T, int] = {}
  for t in ts:
    if t not in result:
      result[t] = 0
    result[t] += 1
  return result


def repeated_elements(ts: Collection[T]) -> FrozenSet[T]:
  """Which of the ts appear in the input collection more than once?"""
  m = multiplicities(ts)
  return frozenset({t for t in ts if m[t] > 1})


def all_equal(ts: Iterable[T]) -> bool:
  try:
    ts = iter(ts)
    first_t = next(ts)
    while True:
      if first_t != next(ts):
        return False
  except StopIteration:
    return True


def empty(ts: Collection[T]) -> bool:
  return len(ts) == 0


def nonempty(ts: Collection[T]) -> bool:
  return len(ts) > 0


def negate(f: Callable[[T], bool]) -> Callable[[T], bool]:
  return lambda t: not f(t)


def disj(fs: Iterable[Callable[[T], bool]]) -> Callable[[T], bool]:
  """Return a function `t -> bool` which is true if any `f(t) == true`."""
  return lambda t: any(f(t) for f in fs)


def implies(p: bool, q: bool) -> bool:
  return not p or q


def without_none(ts: Iterable[Optional[T]]) -> Generator[T, None, None]:
  for t in ts:
    if t is not None:
      yield t


def product(xs: Iterable[float]) -> float:
  answer = 1.0
  for x in xs:
    answer *= x
  return answer


def take_before(
  fail_on: Callable[[T], bool], ts: Iterable[T]) -> Generator[T, None, None]:

  for t in ts:
    if fail_on(t):
      return
    yield t
