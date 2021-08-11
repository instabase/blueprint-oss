"""Scoring for extraction.

WARNING: This documentation may be outdated and/or incomplete.

Blueprint works by sampling many extractions from some extraction-generation
object and keeping the "best" one -- determined by calculating various scores.

First, the *rule score*. A rule R over the fields F1, ..., Fn is essentially a
score function which takes n entities as arguments and returns a number between
0 and 1, representing how-well the rule holds. Then, given an extraction E, the
rule score of E under R is

  rule_score(E, R) = R.score_function(E(F1), ..., E(Fn))

Given a collection of rules Rs = {R1, ..., Rm}, an extraction E, and a field F,
the *field score* of F under E and Rs is

  field_score(F, E, Rs) = product(rule_score(R, E)
                              for R in Rs if F in R.fields)

The *extraction score* for an extraction with field scores Fs at bound node N is

  extraction_score(Fs, N) = sum(Fs) / N.mass

"""

import dataclasses

from functools import reduce
from itertools import chain
from typing import Any, Callable, Collection, Dict, FrozenSet, Iterable, Optional, Tuple
from uuid import uuid4

from .document import Document
from .entity import Entity
from .extraction import Assignment, Extraction, Field, UnrecognizedFieldsError
from .functional import comma_sep, nonempty, pairwise_disjoint, product
from .rule import Atom, AtomScore, Conjunction, Connective, ConnectiveScore, Disjunction, Predicate, Rule, RuleScore, get_atoms, rule_is_decidable


FieldScores = Dict[Field, float]  # These floats should be in [0, 1].


@dataclasses.dataclass(frozen=True)
class ScoredExtraction:
  """An extraction, plus metadata about the extraction's score and how it was
  computed.

  WARNING: It is possible to pass a set of arguments to this class's constructor
  that would put it into an invalid state. See the attributes documentation
  below. Don't call this constructor manually unless you know what you're doing.

  Attributes:
    extraction: The underlying Extraction: a dictionary from fields to entities.
    score: The extraction score.
    field_scores: A dictionary from field to field score for all fields in the
      extraction.
    rule_scores: The rule scores (plus metadata) of all the rules that went
      into computing this extraction's score.
    mass: Mass of this extraction.
  """

  extraction: Extraction
  score: float
  field_scores: FieldScores
  rule_scores: Dict[str, RuleScore]
  mass: float
  uuid: str = str(uuid4())

  @staticmethod
  def build(extraction: Extraction = Extraction(tuple()),
            mass: float = 1,
            base_field_scores: FieldScores = {}) \
              -> 'ScoredExtraction':
    """Generate a default-scored extraction.

    Default-scored extractions are extractions with no rules. All fields will
    have field scores of 1, and the extraction will have an extraction score of
    1 (unless it has no fields -- in which case it will score 0).

    Args:
      extraction: An extraction.
      base_field_scores: See #267.
    """
    return ScoredExtraction(
      extraction=extraction,
      score=0 if len(extraction) == 0 else 1,
      field_scores={field: base_field_scores.get(field, 1.0)
                    for field in extraction.fields},
      mass=mass,
      rule_scores={})

  @property
  def fields(self) -> FrozenSet[Field]:
    return self.extraction.fields

  @property
  def entities(self) -> FrozenSet[Entity]:
    """The entity assignments for this extraction."""
    return frozenset(self.extraction.entities)

  @property
  def is_empty(self) -> bool:
    return self.extraction.is_empty

  @property
  def valid(self) -> bool:
    return all(self.field_is_valid(field) for field in self.fields)

  def field_score(self, field: Field) -> float:
    if field not in self.fields:
      raise UnrecognizedFieldsError(f'field {field} not found in {self}')
    return self.field_scores[field]

  def field_is_valid(self, field: Field) -> bool:
    if field not in self.fields:
      raise UnrecognizedFieldsError(f'field {field} not found in {self}')
    return assignment_is_valid(self[field], self.field_score(field))

  def normalize(self, mass: int) -> 'ScoredExtraction':
    return dataclasses.replace(
      self, score=extraction_score(self.field_scores, mass))

  def __lt__(self, other: 'ScoredExtraction') -> bool:
    """Rank-order extractions from highest- to lowest-scoring.

    Running the comparison in this order makes the spelling of all of the
    algorithms simpler. (Sorting is usually done smallest-to-largest, heaps are
    usually min-heaps.)
    """
    return self.score > other.score

  def __getitem__(self, field: Field) -> Entity:
    """The entity this field is assigned to by this extraction.

    Args:
      field: A field. This should be in the extraction. Check whether it is
        present in the extraction before calling this method.
    """
    return self.extraction[field]

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, ScoredExtraction):
      return False
    return id(self) == id(other)

  def __hash__(self) -> int:
    return id(self).__hash__()

  def __contains__(self, field: Field) -> bool:
    return field in self.extraction

  def __len__(self) -> int:
    return len(self.extraction)

  def prepend_field_score(self, field: Field, s: str) -> str:
    """Given a string, prepend the field score for this field."""
    return f'({self.field_score(field):1.3f}) {s}'

  def point_str(self, field: Field) -> str:
    """A string showing the assignment for this field, with its field score.

    Example output:

      (0.983) net_pay -> "$123.45"
    """
    return self.prepend_field_score(field, str(self.extraction.point(field)))

  def __str__(self) -> str:
    point_strs = comma_sep(self.point_str(field) for field in self.fields)
    return f'[{point_strs}]'


def assignment_is_valid(assignment: Assignment, field_score: float) -> bool:
  """Is it valid to give a field this assignment, if the resulting field score
  is this number?

  An assignment is invalid if its field score is below some cut-off. Extractions
  will be discarded if they have any invalid field assignments.

  It improves accuracy performance to have a badness threshold where we say
  "this is so bad that we will throw it out entirely". At the rule level, this
  is encoded by the tolerances of the rules themselves. (If two things are
  badly-enough misaligned, an alignment rule will score 0.) What
  MINIMUM_FIELD_SCORE captures is extractions where several rules score badly,
  but not badly-enough for any of them to hit 0 individually.

  MINIMUM_FIELD_SCORE is treated as a strict lower bound: any extraction which
  has some nontrivial field score *equal* to this number is considered invalid,
  and will be discarded. The reason is that if it were done otherwise, that is,
  if MINIMUM_FIELD_SCORE were a weak lower bound, then if someone were to set
  this number to 0, to indicate that we don't want to impose a minimum field
  score, there would be an explosion in the number of extractions deemed valid
  at the leaf level, as the code is currently written.
  """
  MINIMUM_FIELD_SCORE = 0.1  # This value is somewhat arbitrary.
  if assignment is None and field_score != 0:
    raise RuntimeError(
      f'assignment to None cannot have non-zero field score {field_score}')
  return assignment is None or field_score > MINIMUM_FIELD_SCORE


def extraction_score(field_scores: FieldScores, mass: int) -> float:
  return sum(field_scores[field] for field in field_scores) / mass


def get_rule_score(
  rule: Rule,
  extraction: Extraction,
  score_cache: Dict[str, RuleScore]) \
    -> RuleScore:
  if rule.uuid in score_cache:
    return score_cache[rule.uuid]
  return rule.rule_score(extraction)


def merge(
  scored_extractions: Collection[ScoredExtraction],
  rules: FrozenSet[Rule],
  fields: FrozenSet[Field],
  mass: int) \
    -> ScoredExtraction:
  """Merge the scored extractions, applying the extra rules."""
  # This checks that the individual extractions' fields don't overlap.
  extraction = Extraction.merge([
    scored_extraction.extraction for scored_extraction in scored_extractions])

  rule_scores: Dict[str, RuleScore] = {}
  field_scores: FieldScores = {}
  for scored_extraction in scored_extractions:
    rule_scores = {**rule_scores, **scored_extraction.rule_scores}
    field_scores = {**field_scores, **scored_extraction.field_scores}

  atom_scores = {atom.uuid: get_rule_score(atom, extraction, rule_scores)
    for atom in filter(lambda R: rule_is_decidable(R, extraction),
      chain.from_iterable(get_atoms(rule) for rule in rules))}
  rule_scores = {**rule_scores, **atom_scores}

  decidable_rules = frozenset(filter(
    lambda R: rule_is_decidable(R, extraction), rules))
  non_decidable_rules = rules - decidable_rules

  # TODO: Also should be able to use cached atom rules when calculating final
  # connective rule score
  decidable_rules_scores = (
      (rule, get_rule_score(rule, extraction, rule_scores))
    for rule in decidable_rules)

  early_exits = tuple(filter(lambda R:
    upper_bound(R, extraction, rule_scores) == 0,
    non_decidable_rules))

  for rule, score in decidable_rules_scores:
    for field in filter(lambda F: F in extraction.fields, rule.fields):
      # FIXME: Floating-point rounding.
      field_scores[field] *= score.score
      rule_scores[rule.uuid] = score

  for rule in early_exits:
    for field in filter(lambda F: F in extraction.fields, rule.fields):
      field_scores[field] = 0.0

  return ScoredExtraction(extraction, extraction_score(field_scores, mass),
                          field_scores, rule_scores, mass)


def upper_bound(rule: Rule,
                extraction: Extraction,
                score_cache: Dict[str, RuleScore]) -> float:
  if rule.uuid in score_cache:
    return score_cache[rule.uuid].score
  elif isinstance(rule, Atom):
    return rule.rule_score(extraction).score \
        if rule_is_decidable(rule, extraction) \
        else 1.0
  elif isinstance(rule, Disjunction):
    return max(
      (upper_bound(sub_rule, extraction, score_cache)
        for sub_rule in rule.rules) or (1.0,))
  else:
    assert isinstance(rule, Conjunction)
    return product(
      upper_bound(sub_rule, extraction, score_cache)
        for sub_rule in rule.rules)


def leaf_score(assignment: Assignment,
               predicates: Iterable[Predicate],
               document: Document) \
                -> Tuple[float, Dict[Predicate, RuleScore]]:
  """A field score at a leaf node, with respect to these predicates.

  Returns:
    The field score, and the RuleScore objects corresponding to the rule score
    computations. If assignment is None, then the field score is 0.
  """
  initializer = 0.0 if assignment is None else 1.0
  atom_scores = {
    predicate:
      predicate.score((assignment,), document)
      if assignment is not None else AtomScore(1.0)
    for predicate in predicates
  }
  field_score = reduce(
    lambda p, q: p * q,
    (atom_score.score for atom_score in atom_scores.values()), initializer)
  return (field_score, atom_scores)
