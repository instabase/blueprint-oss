"""Rule data structures.

The actual rules you can use to describe document structure -- and their
documentation -- are in `blueprint.rules`.
"""

import dataclasses

from enum import Enum
from itertools import chain
from typing import Any, Callable, Collection, Dict, FrozenSet, Iterable, Optional, Tuple, Type, Union
from uuid import uuid4

from .document import Document
from .entity import Entity
from .extraction import Extraction, Field
from .functional import pairs, product
from .spatial_formula import Formula


AtomDegree = Union[int, str] # str should be Literal['ANY'], Literal requires Python 3.8.


def _default_uuid() -> str:
  return str(uuid4())

class Lenience(Enum):
  LOW: float = 0.1
  MEDIUM: float = 0.3
  HIGH: float = 0.5
  NOT_APPLICABLE: float = 1.0

  def __float__(self) -> float:
    return self.value

@dataclasses.dataclass(frozen=True)
class AtomScore:
  score: float
  type: str = 'atom_score'


@dataclasses.dataclass(frozen=True)
class ConnectiveScore:
  score: float
  rule_scores: Dict[str, 'RuleScore']
  type: str


@dataclasses.dataclass(frozen=True)
class ConjunctionScore(ConnectiveScore):
  def __init__(
    self,
    score: float,
    rule_scores: Dict[str, 'RuleScore'],
  ):
    object.__setattr__(self, 'score', score)
    object.__setattr__(self, 'rule_scores', rule_scores)
    object.__setattr__(self, 'type', 'conjunction_score')

  @staticmethod
  def build(rule_scores: Dict[str, 'RuleScore']) -> 'ConjunctionScore':
    score = product(rule_score.score for rule_score in rule_scores.values())
    return ConjunctionScore(score, rule_scores)


@dataclasses.dataclass(frozen=True)
class DisjunctionScore(ConnectiveScore):
  def __init__(
    self,
    score: float,
    rule_scores: Dict[str, 'RuleScore'],
  ):
    object.__setattr__(self, 'score', score)
    object.__setattr__(self, 'rule_scores', rule_scores)
    object.__setattr__(self, 'type', 'disjunction_score')

  @staticmethod
  def build(rule_scores: Dict[str, 'RuleScore']) -> 'DisjunctionScore':
    score = max(rule_score.score for rule_score in rule_scores.values() or [])
    return DisjunctionScore(score, rule_scores)


RuleScore = Union[
  AtomScore,
  ConnectiveScore,
]


class DegreeError(ValueError):
  """A rule, function, or predicate was passed an unexpected number of
  arguments.

  For example, this can happen if a predicate is passed an unexpected number of
  fields, or a rule's score function is passed an unexpected number of entities.
  """
  pass


@dataclasses.dataclass(frozen=True)
class Predicate:
  """A rule predicate.

  For example: "is on the left side of the page", or "are bottom-aligned". In
  the rule "'period_begin' is a date", the subject is "'period_begin'" and the
  predicate is "is a date". In Blueprint code, this is expressed as
  `is_date('period_begin')`, where `is_date` is a `Predicate`.

  A Predicate applied to an appropriate number of fields gives a Rule.
  """

  name: str
  uuid: str

  @property
  def degree(self) -> AtomDegree:
    """The number of fields this predicate can be applied to.

    The score function and phi are defined for inputs consisting of this many
    entities and fields, respectively.

    This is either a positive integer or 'ANY'.
    """
    raise NotImplementedError

  def score(self, entities: Tuple[Entity, ...], document: Document) \
      -> RuleScore:
    raise NotImplementedError

  def phi(self, fields: Tuple[Field, ...]) -> Formula:
    """A formula which evaluates to true for any extraction for which this
    predicate has a positive rule score.

    This formula should be thought of as a weakening of the rule.

    You probably don't need to worry about this if you are just writing simple
    custom rules.
    """
    return True
  
  def leniency(self) -> float:
    """A formula that approximates how 'permissive' this predicate is; conceptually, 
    what fraction of possible assignments this predicate is expected to not eliminate.
    
    Right now, these are simply static values that are just based on guesswork and 
    trial and error, but better accuracy might improve performance.
    """
    return float(Lenience.MEDIUM)

  def __call__(self, *fields: Field) -> 'Atom':
    """Builds a rule from this predicate by applying it to the given fields.
    You can also use the Rule constructor, but often using this method results
    in more-natural-looking code. For example, if you have a Predicate object
    called are_left_aligned, it's very natural to say `are_left_aligned(field1,
    field2)`, as opposed to `Rule((field1, field2), are_left_aligned)`, although
    the second syntax is also allowed.
    """
    if self.degree != 'ANY' and len(fields) != self.degree:
      raise DegreeError(
        f'cannot bind {len(fields)} fields to a degree-{self.degree} rule')
    return Atom(fields, self)

  def __hash__(self) -> int:
    return id(self).__hash__()

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, Predicate):
      return False
    # FIXME: We should return true if two predicates are semantically identical,
    # even if they happen to be different Python objects.
    return id(self) == id(other)

  def __str__(self) -> str:
    return self.name


@dataclasses.dataclass(frozen=True)
class Degree1Predicate(Predicate):
  """A degree-1 predicate."""

  @property
  def degree(self) -> int:
    return 1

  def leniency(self) -> float:
    return float(Lenience.NOT_APPLICABLE)
    # Currently, leniency is conceptualized as how many possible assignments
    # a predicate will permit. However, deciding how many possible
    # assignments a field has already checks that any applicable
    # Degree1Predicates have score > 0. So, unless this predicate frequently
    # gives very low nonzero scores, its leniency should be close to 1.

@dataclasses.dataclass(frozen=True)
class Degree2Predicate(Predicate):
  """A degree-2 predicate."""

  @property
  def degree(self) -> int:
    return 2


@dataclasses.dataclass(frozen=True)
class Atom:
  """A rule.

  Attributes:
    fields: The fields this rule applies to.
    predicate: This rule's predicate. See the Predicate docs.
    uuid: This rule's uuid.

  Example code:
    Rule(('net_pay_label', 'net_pay_value'),
      are_arranged(Direction.LEFT_TO_RIGHT))

    Rule(('net_pay_value', ), is_dollar_amount)

    # The above is the same as:
    is_dollar_amount('net_pay_value')
  """
  fields: Tuple[Field, ...]
  predicate: Predicate
  uuid: str = dataclasses.field(default_factory=_default_uuid)
  name: Optional[str] = None
  type: str = 'atom'

  document: Optional[Document] = None

  @property
  def phi(self) -> Formula:
    return self.predicate.phi(self.fields)

  def with_uuid(self, uuid: Optional[str]) -> 'Atom':
    return dataclasses.replace(self, uuid=uuid)

  def with_document(self, document: Document) -> 'Atom':
    return dataclasses.replace(self, document=document)

  def validate(self) -> None:
    if not isinstance(self.fields, tuple):
      raise TypeError(
        f'fields {self.fields} of rule {self} must be a tuple, '
        f'not {type(self.fields)}')

    for field in self.fields:
      if not isinstance(field, Field):
        raise TypeError(
          f'field {field} of rule {self} must be a Field, '
          f'not {type(field)}')

  def rule_score(self, extraction: Extraction) -> RuleScore:
    """Computes the rule score of the given extraction."""
    if any(field not in extraction.fields for field in self.fields):
      return AtomScore(1.0)
    if self.document is None:
      raise RuntimeError(f'document not bound to rule {self}')
    return self.predicate.score(
      tuple(extraction[field] for field in self.fields), self.document)

  def __hash__(self) -> int:
    return (self.fields, self.predicate).__hash__()

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, Atom):
      return False
    return (self.fields, self.predicate) == (other.fields, other.predicate)

  def __str__(self) -> str:
    return '[{}] {}'.format(', '.join(map(str, self.fields)), self.predicate)


@dataclasses.dataclass(frozen=True)
class Connective:
  rules: Tuple['Rule', ...]
  name: Optional[str] = None
  uuid: str = dataclasses.field(default_factory=_default_uuid)

  # TODO: Make BoundRule instead.
  document: Optional[Document] = None

  @property
  def fields(self) -> Tuple[Field, ...]:
    return tuple(frozenset(
      chain.from_iterable(rule.fields for rule in self.rules)))

  @property
  def atoms(self) -> FrozenSet[Atom]:
    def get_atoms(child: Rule) -> FrozenSet[Atom]:
      if isinstance(child, Atom):
        return frozenset({child})
      return frozenset(chain.from_iterable(get_atoms(rule)
        for rule in child.rules))
    return frozenset(chain.from_iterable(get_atoms(child)
      for child in self.rules))

  @property
  def atom_field_sets(self) -> Tuple[Tuple[Field, ...], ...]:
    return tuple(atom.fields for atom in self.atoms)

  def with_document(self, document: Document) -> 'Connective':
    return dataclasses.replace(self, document=document,
      rules=tuple(rule.with_document(document) for rule in self.rules))

  def rule_score(self, extraction: Extraction) -> RuleScore:
    raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class Conjunction(Connective):
  type: str = 'conjunction'

  def rule_score(self, extraction: Extraction) -> RuleScore:
    sub_scores = {rule.uuid: rule.rule_score(extraction) for rule in self.rules}
    return ConjunctionScore.build(sub_scores)


@dataclasses.dataclass(frozen=True)
class Disjunction(Connective):
  type: str = 'disjunction'

  def rule_score(self, extraction: Extraction) -> RuleScore:
    sub_scores = {rule.uuid: rule.rule_score(extraction) for rule in self.rules}
    return DisjunctionScore.build(sub_scores)


Rule = Union[Atom, Connective]


def any_rule_holds(*rules: Rule) -> Rule:
  return Disjunction(rules)


def all_rules_hold(*rules: Rule) -> Rule:
  return Conjunction(rules)


def build_connective(
  fields: Tuple[Field, ...],
  predicate_type: Type,
  connective_type: Type) -> Rule:
  """Build conjunction of pairwise atoms for a given predicate and some fields.
  """
  def build_atom(field_1: Field, field_2: Field) -> Atom:
    return Atom(fields=(field_1, field_2), predicate=predicate_type())
  if len(fields) < 2:
    raise ValueError(f'rule constructor for predicate {predicate_type().name} '
                      'must take at least 2 fields')
  if len(fields) == 2:
    return build_atom(*fields)
  return connective_type(rules=tuple(build_atom(*pair)
    for pair in pairs(fields)), name=predicate_type().name)


def build_conjunction(fields: Tuple[Field, ...], predicate: Type[Predicate]) \
    -> Rule:
  return build_connective(fields, predicate, Conjunction)


def build_disjunction(fields: Tuple[Field, ...], predicate: Type[Predicate]) \
    -> Rule:
  return build_connective(fields, predicate, Disjunction)


def get_atoms(rule: Rule) -> FrozenSet[Atom]:
  if isinstance(rule, Atom):
    return frozenset({rule})
  assert isinstance(rule, Connective)
  return rule.atoms


def rule_is_decidable(rule: Rule, extraction: Extraction) -> bool:
  return extraction.fields.issuperset(frozenset(rule.fields))
