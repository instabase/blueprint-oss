from typing import Tuple

from ..entity import Date, Entity, Text

from .type_scoring import date_likeness


MINIMUM_SCORE = 0.7


def get_dates(entities: Tuple[Entity, ...]) -> Tuple[Date, ...]:
  """Get date-like entities from the given Entities.

  Args:
    entities: Should be Words or Phrases.
  """
  def make_date(E: Entity) -> Date:
    assert isinstance(E, Text)
    score, _ = date_likeness(E.text)
    return Date(E.bbox, E.text, tuple(E.entity_words()), score)
  return tuple(filter(lambda E: (E.likeness_score or 0) >= MINIMUM_SCORE,
    map(make_date, entities)))
