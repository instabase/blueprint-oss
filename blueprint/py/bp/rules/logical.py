"""Logic-related Blueprint rules."""

from dataclasses import dataclass, replace
from typing import Callable, Iterable, Optional, Tuple
from uuid import uuid4

from ..document import Document
from ..entity import Entity
from ..extraction import Field
from ..rule import AtomDegree, AtomScore, DegreeError, Predicate, RuleScore
from ..spatial_formula import (
  Conjunction as LogicalConjunction,
  Disjunction as LogicalDisjunction,
  Formula,
  simplify,
)


def _prod(xs: Iterable[float]) -> float:
  answer = 1.0
  for x in xs:
    answer *= x
  return answer


def _check_score_degree(entities: Tuple[Entity, ...],
                        degree: AtomDegree) -> None:
  if degree != 'ANY' and len(entities) != degree:
    raise DegreeError('scoring wrong number of entities; '
      f'expected {degree}, got {len(entities)}')


def _check_phi_degree(fields: Tuple[Field, ...],
                      degree: AtomDegree) -> None:
  if degree != 'ANY' and len(fields) != degree:
    raise DegreeError('applying to wrong number of fields; '
      f'expected {degree}, got {len(fields)}')


@dataclass(frozen=True)
class AllHold(Predicate):
  wrapped_predicates: Tuple[Predicate, ...]
  degree_: AtomDegree

  def __init__(
    self,
    wrapped_predicates: Tuple[Predicate, ...],
    degree_: AtomDegree,
    name: str = 'penalize',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'wrapped_predicates', wrapped_predicates)
    object.__setattr__(self, 'degree_', degree_)

  @property
  def degree(self) -> AtomDegree:
    return self.degree_

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    _check_score_degree(entities, degree=self.degree)
    results = tuple(predicate.score(entities, doc)
      for predicate in self.wrapped_predicates)
    score = _prod(result.score for result in results)
    return AtomScore(score)

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    _check_phi_degree(fields, degree=self.degree)
    return simplify(LogicalConjunction(
      predicate.phi(fields) for predicate in self.wrapped_predicates))


def all_hold(*predicates: Predicate) -> Predicate:
  """Says that all of its subrules hold.

  This is the analog of `and` in a normal programming language.

  Technically, the resulting score is the product of the scores of the subrules.
  """

  degrees = set(filter(
    lambda degree: degree != 'ANY',
    (predicate.degree for predicate in predicates)))
  if len(degrees) > 1:
    raise DegreeError('all input predicates to all_hold must have same degree; '
      f'error in {predicates}')
  degree = next(iter(degrees)) if degrees else 'ANY'

  return AllHold(
    name='all_hold({})'.format(', '.join(sorted(map(str, predicates)))),
    wrapped_predicates=predicates,
    degree_=degree)


@dataclass(frozen=True)
class AnyHolds(Predicate):
  wrapped_predicates: Tuple[Predicate, ...]
  degree_: AtomDegree

  def __init__(
    self,
    wrapped_predicates: Tuple[Predicate, ...],
    degree_: AtomDegree,
    name: str = 'penalize',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'wrapped_predicates', wrapped_predicates)
    object.__setattr__(self, 'degree_', degree_)

  @property
  def degree(self) -> AtomDegree:
    return self.degree_

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    _check_score_degree(entities, degree=self.degree)
    results = tuple(predicate.score(entities, doc)
      for predicate in self.wrapped_predicates)
    score = max(result.score for result in results)
    return AtomScore(score)

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    _check_phi_degree(fields, degree=self.degree)
    return simplify(LogicalDisjunction(
      predicate.phi(fields) for predicate in self.wrapped_predicates))


def any_holds(*predicates: Predicate) -> Predicate:
  """Says that at least one of its subrules holds.

  This is the analog of `or` in a normal programming langauge.

  Technically, the score is the maximum of the scores of the subrules.
  """

  degrees = set(
      filter(
          lambda degree: degree != 'ANY',
          (predicate.degree for predicate in predicates)))
  if len(degrees) > 1:
    raise DegreeError(
        f'all input rules must have same degree; error in {predicates}')
  degree = next(iter(degrees)) if degrees else 'ANY'

  return AnyHolds(
    name='any_holds({})'.format(', '.join(sorted(map(str, predicates)))),
    wrapped_predicates=predicates,
    degree_=degree)


@dataclass(frozen=True)
class AreDisjoint(Predicate):
  """Says that two fields' assignments have no words in common.

  Scores 0 if the two fields' assignments have any words in common, 1 otherwise.

  NOTE: This doesn't check whether the same *string* appears in the two field
  assignments: it checks whether the two field assignments *share any actual
  typeset words on the page*.
  """

  def __init__(
    self,
    name: str = 'are_disjoint',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  @property
  def degree(self) -> int:
    return 2

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities

    if not set(E1.entity_words()) & set(E2.entity_words()):
      return AtomScore(1)
    else:
      return AtomScore(0)


are_disjoint = AreDisjoint()


@dataclass(frozen=True)
class Nop(Predicate):
  """No op. Will always score 1."""

  def __init__(
    self,
    name: str = 'nop',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  @property
  def degree(self) -> AtomDegree:
    return 'ANY'

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    return AtomScore(1)


@dataclass(frozen=True)
class Penalize(Predicate):
  wrapped_predicate: Predicate
  max_score: float

  def __init__(
    self,
    wrapped_predicate: Predicate,
    max_score: float = 0.7,
    name: str = 'penalize',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'wrapped_predicate', wrapped_predicate)
    object.__setattr__(self, 'max_score', max_score)

  @property
  def degree(self) -> AtomDegree:
    return self.wrapped_predicate.degree

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    result = self.wrapped_predicate.score(entities, doc)
    # FIXME: Once we support this in Studio, add back in metadata for
    # pre-penalize score (same for non-fatal below)
    return AtomScore(min(result.score, self.max_score))

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    return self.wrapped_predicate.phi(fields)


def penalize(wrapped_predicate: Predicate, max_score: float = 0.7) \
    -> Predicate:
  return Penalize(wrapped_predicate, max_score)


@dataclass(frozen=True)
class NonFatal(Predicate):
  wrapped_predicate: Predicate
  min_score: float

  def __init__(
    self,
    wrapped_predicate: Predicate,
    min_score: float = 0.5,
    name: str = 'non_fatal',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'wrapped_predicate', wrapped_predicate)
    object.__setattr__(self, 'min_score', min_score)

  @property
  def degree(self) -> AtomDegree:
    return self.wrapped_predicate.degree

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    result = self.wrapped_predicate.score(entities, doc)
    return AtomScore(max(result.score, self.min_score))


def non_fatal(wrapped_predicate: Predicate, min_score: float = 0.5) \
    -> Predicate:
  return NonFatal(wrapped_predicate, min_score)


@dataclass(frozen=True)
class Negate(Predicate):
  wrapped_predicate: Predicate

  def __init__(
    self,
    wrapped_predicate: Predicate,
    name: str = 'negate',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'wrapped_predicate', wrapped_predicate)

  @property
  def degree(self) -> AtomDegree:
    return self.wrapped_predicate.degree

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    result = self.wrapped_predicate.score(entities, doc)
    return replace(result, score=(1 - result.score))


def negate(wrapped_predicate: Predicate) -> Predicate:
  return Negate(wrapped_predicate)
