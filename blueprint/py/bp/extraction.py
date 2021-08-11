"""Data structures describing extraction results.

Typically an extraction is represented as a tuple of field-entity pairs.
"""

import json

from dataclasses import asdict, dataclass, replace
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import Any, Collection, Dict, FrozenSet, Generator, Iterable, Optional, Set, Tuple, TypeVar

from .entity import Entity, entity_resolver
from .geometry import BBox
from .instantiate import instantiate


"""An ID for "something we wish to extract" in a document.

If you want to extract a thing from a document (a numeric value, an anchor, some
text, whatever), you need to represent it as an extraction field. An extraction
field is just a name for a thing-to-be-extracted. You can think of a field as
the analog of a variable in another modeling language. A Blueprint extraction
consists of assignments from a set of fields to entities in a document.
"""
Field = str


Assignment = Optional[Entity]


T = TypeVar('T')


class MissingFieldsError(KeyError):
  """A function or operation was passed a collection of fields that was missing
  required fields."""
  pass


class OverlappingFieldsError(KeyError):
  """A function or operation was passed collections of fields that overlap
  unexpectedly."""
  pass


class UnrecognizedFieldsError(KeyError):
  """A function or operation was passed unrecognized fields."""
  pass


@dataclass(frozen=True)
class ExtractionPoint:
  """A (field, entity) pair."""
  field: Field
  entity: Entity

  @property
  def assignment_text(self) -> Optional[str]:
    """The entity text, or None."""
    return self.entity.entity_text

  @property
  def assignment_str(self) -> str:
    """The entity text in quotes, or 'None'."""
    return f'"{self.entity}"'

  def __str__(self) -> str:
    return f'{self.field} -> {self.entity.entity_text}'


@dataclass(frozen=True)
class Extraction:
  """An assignment from some fields to some entities in some document.

  When we say we "want to extract the net and gross pay", another way of framing
  the problem is that we want something like this:

    (
      ('net_pay', <something in the document>),
      ('gross_pay', <something in the document>),
    )

  We call such a tuple an *extraction*. Extractions can be good or bad,
  "right" or "wrong". The goal of a Blueprint model is to find good
  extractions. Blueprint's library of rules enable you to describe good
  extractions look and behave, by listing rules that the fields should follow.
  """

  assignments: Tuple[ExtractionPoint, ...]

  @property
  def fields(self) -> FrozenSet[Field]:
    """The fields for which this extraction has entity assignments."""
    return frozenset(self.build_dictionary().keys())

  @property
  def entities(self) -> FrozenSet[Entity]:
    """The entity assignments for this extraction."""
    return frozenset(self.build_dictionary().values())

  @property
  def is_empty(self) -> bool:
    return self.assignments == tuple()

  @lru_cache(maxsize=None)
  def build_dictionary(self) -> Dict[Field, Entity]:
    return {point.field: point.entity for point in self.assignments}

  def __bool__(self) -> bool:
    return not self.is_empty

  def __getitem__(self, field: Field) -> Entity:
    """The entity this field is assigned to under this extraction.

    Args:
      field: A field. This must be present in the extraction. Check whether the
        field is in the extraction before calling this method.
    """
    dictionary = self.build_dictionary()
    if field not in dictionary:
      raise UnrecognizedFieldsError(f'{field} not found in {self}')
    return dictionary[field]

  def __eq__(self, other: Any) -> bool:
    return isinstance(other, Extraction) and \
            frozenset(self.assignments) == frozenset(other.assignments)

  def __contains__(self, field: Field) -> bool:
    return field in self.fields

  def __len__(self) -> int:
    return len(self.assignments)

  def point(self, field: Field) -> Optional[ExtractionPoint]:
    """The (field, entity) pair for this field in this extraction.

    May return (field, None).

    This is mostly used for logging/printing.

    Args:
      field: A field. If this field is not present in the extraction, this
        function returns (field, None).
    """
    return ExtractionPoint(field, self[field]) \
        if field in self.build_dictionary() else None

  def points(self) -> Generator[ExtractionPoint, None, None]:
    """The points in this extraction, sorted by field name."""
    for field in sorted(self.fields):
      point = self.point(field)
      if point is not None:
        yield point

  @staticmethod
  def merge(extractions: Collection['Extraction']) -> 'Extraction':
    """Combine several extractions into one.

    Args:
      extractions: Input extractions. These must not have any fields in common.
    """
    def pairwise_disjoint(tss: Iterable[Iterable[T]]) -> bool:
      s: Set[T] = set()
      for t in chain.from_iterable(tss):
        if t in s:
          return False
        s.add(t)
      return True

    if not pairwise_disjoint(extraction.fields for extraction in extractions):
      raise OverlappingFieldsError(f'cannot merge extractions {extractions}')

    return Extraction(tuple(chain.from_iterable(extraction.assignments
        for extraction in extractions)))

  def __str__(self) -> str:
    return f'[{", ".join(map(str, self.points()))}]'

  def __repr__(self) -> str:
    return f'<Extraction({", ".join(map(str, self.points()))})>'


def load_extraction(path: Path) -> Extraction:
  with path.open() as f:
    return load_extraction_from_json(json.load(f))


def load_extraction_from_json(blob: Dict) -> Extraction:
  return instantiate(
    Extraction,
    blob,
    base_classes={Entity},
    derived_class_resolver=entity_resolver)
