import functools

from dataclasses import dataclass
from typing import Callable, FrozenSet, Generator, List, Optional, Tuple, Union

from .document import DocRegion, Document
from .extraction import Field
from .scoring import ScoredExtraction
from .spatial_formula import Conjunction, DocRegionTerm, Disjunction, Intersect, IsContained, Literal, Formula


@dataclass(frozen=True)
class _Conjunction:
  """State that a document region is a subset of the given superset (if present)
  and meets the all of the intersection sets (if present).

  Values of None here mean 'condition not considered'. This is confusing: in
  some places, None means 'empty set'.

  Either one of these is set, or both are. If both are, each intersection set
  is a subset of superset.
  """
  superset: Optional[DocRegion]
  intersection_sets: Optional[Tuple[DocRegion, ...]]


@dataclass(frozen=True)
class DocRegionRestriction:
  """Describe a document region in disjunctive normal form."""

  # These are the terms of a disjunction.
  conjunctions: Tuple[_Conjunction, ...]


def get_doc_region_restriction(field: Field,
                               M_feeder: ScoredExtraction,
                               phi: Disjunction[Conjunction[Literal]],
                               document: Document) \
                                 -> Union[DocRegionRestriction, bool]:
  """Given a spatial formula all of whose predicates are over
  extraction[field].doc_region and M_feeder[field0].doc_region for field0 in
  M_feeder.fields, describe the document regions where extraction[field] is
  allowed to be, according to phi, in DNF, where each predicate states either
  that extraction[field].doc_region is a subset of a fixed document region, or
  that it intersects a fixed document region."""

  def get_doc_region(term: DocRegionTerm) -> Union[Optional[DocRegion]]:
    """A return value of None here means 'empty set'."""
    doc_region = DocRegion.build(document, M_feeder[term.field].bbox)
    assert doc_region
    if term.transformation is not None:
      return term.transformation(doc_region)
    return doc_region

  def process_intersect(intersect: Intersect) -> Union[DocRegion, bool]:
    non_field_terms = tuple(
        filter(lambda term: term.field != field, intersect.terms))
    field_terms = tuple(
        filter(lambda term: term.field == field, intersect.terms))
    assert all(term.transformation is None for term in field_terms)

    # For any field mapped to None, any term involving it is True by convention.
    # FIXME: These types should be more explicit. None is overloaded a lot in this logic.
    # FIXME: It would be cleaner for get_doc_region to return an ANYTHING literal.
    non_field_terms = tuple(
        filter(lambda term: term.field in M_feeder.fields, non_field_terms))

    if field_terms and not non_field_terms:
      return True

    intersection = DocRegion.intersection(
      map(get_doc_region, non_field_terms))
    if intersection is None:
      return False
    if not field_terms:
      return True
    return intersection

  def process_is_contained(
      is_contained: IsContained) -> Union[DocRegion, bool]:
    assert is_contained.rhs.field != field

    # For any field mapped to None, any term involving it is True by convention.
    # FIXME: These types should be more explicit. None is overloaded a lot in this logic.
    # FIXME: It would be cleaner for get_doc_region to return an ANYTHING literal.
    for field0 in (is_contained.lhs.field, is_contained.rhs.field):
      if field0 == field:
        continue
      if field0 not in M_feeder.fields:
        return True

    rhs = get_doc_region(is_contained.rhs)

    if is_contained.lhs.field == field:
      assert is_contained.lhs.transformation is None
      return rhs if rhs is not None else False
    else:
      lhs = get_doc_region(is_contained.lhs)
      if lhs is None:
        return True
      if rhs is None:
        return False
      return rhs.contains_doc_region(lhs)

  def process_conjunction(
      conjunction: Conjunction[Literal]) -> Union[_Conjunction, bool]:
    """The logic of this method is very confusing."""

    superset: Optional[DocRegion] = None
    intersection_sets: Optional[Tuple[DocRegion, ...]] = None

    for literal in conjunction.formulas:
      if isinstance(literal, bool):
        if literal is False:
          return False
      elif isinstance(literal, Intersect):
        result = process_intersect(literal)
        if isinstance(result, bool):
          if result is False:
            return False
        else:
          if intersection_sets is None:
            intersection_sets = (result,)
          else:
            intersection_sets += (result,)
      elif isinstance(literal, IsContained):
        result = process_is_contained(literal)
        if isinstance(result, bool):
          if result is False:
            return False
        else:
          if superset is None:
            superset = result
          else:
            superset = DocRegion.intersection([superset, result])
            # FIXME: This is super confusing.
            if superset is None:
              return False

    if superset is not None and intersection_sets is not None:
      intersection_sets_ = tuple(DocRegion.intersection(
        [superset, intersection_set]) for intersection_set in intersection_sets)
      if any(intersection_set is None
          for intersection_set in intersection_sets_):
        return False
      intersection_sets = tuple(intersection_set
        for intersection_set in intersection_sets_
        if intersection_set is not None)

    if superset is None and intersection_sets is None:
      return True

    return _Conjunction(superset, intersection_sets)

  conjunctions: List[_Conjunction] = []
  for conjunction in map(process_conjunction, phi.formulas):
    if conjunction is True:
      return True
    if conjunction is False:
      continue
    assert not isinstance(conjunction, bool)
    conjunctions.append(conjunction)

  if not conjunctions:
    return False

  return DocRegionRestriction(tuple(conjunctions))
