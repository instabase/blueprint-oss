from typing import Iterable, Tuple

from ..document import Document
from ..entity import DollarAmount, Entity, Text

from .type_scoring import dollar_amount_likeness


MINIMUM_SCORE = 0.5


def phrase_subsequences(E: Text) -> Iterable[Text]:
  """Yields subsequence of this phrase.
  Each subphrase is a new Text entity, except for the subphrase which
  spans this entity's children, which is the entity itself.
  """
  words = E.words
  for i in range(len(words)):
    for j in range(i + 1, len(words) + 1):
      if (j - i) == len(words):
        yield E
      else:
        yield Text.from_words(tuple(words[i:j]))


def score_usd(dollar_candidate: Text) -> float:
  def XXX_hack(score: float) -> float:  # ...
    return min(1, max(0, score - 0.01 + 0.01 * len(dollar_candidate.words) / 10))

  score = XXX_hack(dollar_amount_likeness(dollar_candidate.text))
  if score == 0:
    return score

  # FIXME: Janky. We artificially inflate the scores of multi-word phrases
  # which are themselves dollar-amount-like, in order to treat them
  # preferentially at the structuring level. This also ensures that if there
  # are multiple phrases having the same high-scoring child, then the phrase
  # that's most dollar-amount-like considered in its own right will have the
  # highest score.
  child_scores = tuple(
    dollar_amount_likeness(child.text) for child in
    phrase_subsequences(dollar_candidate)
  )
  # This is not the right way to achieve this goal.
  score = max(child_score + (1 - child_score) * score
    for child_score in child_scores)
  return score


def get_dollar_amounts(entities: Tuple[Entity, ...]) \
    -> Tuple[DollarAmount, ...]:
  """Get dollar-amount-like entities from the given Entities. Entities should be
  of type Text."""

  def get_dollar_score(E: Text) -> float:
    return score_usd(E)
  def make_dollar_amount(E: Entity) -> DollarAmount:
    assert isinstance(E, Text)
    words = tuple(E.entity_words())
    return DollarAmount(
      E.bbox, E.text, words, likeness_score=get_dollar_score(E))

  return tuple(filter(lambda E: (E.likeness_score or 0) >= MINIMUM_SCORE,
    map(make_dollar_amount, entities)))
