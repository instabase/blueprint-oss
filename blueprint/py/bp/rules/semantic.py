"""Semantic rules."""

from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import uuid4

from ..document import Document
from ..entity import Address, Date, DollarAmount, Entity, PersonName, Text
from ..rule import AtomScore, Degree1Predicate, DegreeError, RuleScore


@dataclass(frozen=True)
class IsAddress(Degree1Predicate):
  """Says that a field is an address."""

  def __init__(
    self,
    name: str = 'is_address',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    entity = entities[0]
    if not isinstance(entity, Address):
      return AtomScore(0)
    return AtomScore(entity.likeness_score or 0)


@dataclass(frozen=True)
class IsDate(Degree1Predicate):
  """Says that a field is a date."""

  def __init__(
    self,
    name: str = 'is_date',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    entity = entities[0]
    if not isinstance(entity, Date):
      return AtomScore(0)
    return AtomScore(entity.likeness_score or 0)


@dataclass(frozen=True)
class IsDollarAmount(Degree1Predicate):
  """Says that a field is a dollar amount."""

  def __init__(
    self,
    name: str = 'is_dollar_amount',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    entity = entities[0]
    if not isinstance(entity, DollarAmount):
      return AtomScore(0)
    return AtomScore(entity.likeness_score or 0)


@dataclass(frozen=True)
class IsEntirePhrase(Degree1Predicate):
  """Says that a field's assignment consists of an entire horizontal phrase.

  This basically says to include all of the words that are part of the same
  stream of text, on a single line. It does *not* say to include the entire
  horizontal line in the INPUT_COL sense: if there is text that is separated by
  a lot of whitespace, it will not be considered to be part of the same phrase.

  In other words, this rule prevents assigning a field to a single word (or a
  sequence of words) which is properly contained in a larger semantic phrase.

  When calculating the score, we multiply in our estimate for how good a phrase
  this is, based on things like variance in line height or average character
  width.
  """

  def __init__(
    self,
    name: str = 'is_entire_phrase',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    entity = entities[0]
    if not isinstance(entity, Text):
      return AtomScore(0)
    return AtomScore(entity.maximality_score or 0)


@dataclass(frozen=True)
class IsPersonName(Degree1Predicate):
  """Says that a field is a person name."""

  def __init__(
    self,
    name: str = 'is_person_name',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    entity = entities[0]
    if not isinstance(entity, PersonName):
      return AtomScore(0)
    return AtomScore(entity.likeness_score or 0)


is_address = IsAddress()
is_date = IsDate()
is_dollar_amount = IsDollarAmount()
is_entire_phrase = IsEntirePhrase()
is_person_name = IsPersonName()
