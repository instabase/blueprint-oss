import dataclasses

from itertools import chain, product
from typing import Any, Callable, FrozenSet, Generator, Generic, Iterable, Optional, Tuple, TypeVar, Union

from .extraction import Field
from .document import DocRegion


T = TypeVar('T', bound='Formula')


@dataclasses.dataclass(frozen=True)
class DocRegionTerm:
  field: Field
  transformation: Optional[Callable[[DocRegion], Optional[DocRegion]]] = None

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, DocRegionTerm):
      return False
    return id(self) == id(other)

  def __hash__(self) -> int:
    return id(self).__hash__()

  def __str__(self) -> str:
    pr = "DocRegion({})".format(self.field)
    return "T({})".format(pr) if self.transformation is not None else pr


class Intersect:

  def __init__(self, terms: Iterable[DocRegionTerm]):
    self.terms = frozenset(terms)

  terms: FrozenSet[DocRegionTerm]

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, IsContained):
      return False
    return id(self) == id(other)

  def __hash__(self) -> int:
    return id(self).__hash__()

  def __str__(self) -> str:
    if not self.terms:
      return "(empty intersection)"
    return "({}≠∅)".format("∩".join(map(str, self.terms)))


@dataclasses.dataclass(frozen=True)
class IsContained:
  lhs: DocRegionTerm
  rhs: DocRegionTerm

  @property
  def terms(self) -> FrozenSet[DocRegionTerm]:
    return frozenset((self.lhs, self.rhs))

  def __eq__(self, other: Any) -> bool:
    if not isinstance(other, IsContained):
      return False
    return id(self) == id(other)

  def __hash__(self) -> int:
    return id(self).__hash__()

  def __str__(self) -> str:
    return "({}⊆{})".format(self.lhs, self.rhs)


Predicate = Union[Intersect, IsContained]
Literal = Union[Predicate, bool]


class Conjunction(Generic[T]):

  def __init__(self, formulas: Iterable[T]):
    self.formulas = frozenset(formulas)

  formulas: FrozenSet[T]

  def __str__(self) -> str:
    return "({})".format("∧".join(map(str, self.formulas)))


class Disjunction(Generic[T]):

  def __init__(self, formulas: Iterable[T]):
    self.formulas = frozenset(formulas)

  formulas: FrozenSet[T]

  def __str__(self) -> str:
    return "({})".format("∨".join(map(str, self.formulas)))


Formula = Union[Conjunction, Disjunction, Literal]


def doc_region_terms_with_multiplicity(
    f: Formula) -> Generator[DocRegionTerm, None, None]:
  if isinstance(f, bool):
    pass
  if isinstance(f, Conjunction) or isinstance(f, Disjunction):
    yield from chain.from_iterable(
        doc_region_terms_with_multiplicity(formula) for formula in f.formulas)
  if isinstance(f, Intersect) or isinstance(f, IsContained):
    yield from f.terms


def split_by_type(fs: Iterable[Formula]) \
    -> Tuple[Generator[Literal, None, None],
             Generator[Conjunction, None, None],
             Generator[Disjunction, None, None]]:
  fs = tuple(fs)
  literals = filter(
    lambda f: isinstance(f, bool)
           or isinstance(f, Intersect)
           or isinstance(f, IsContained), fs)
  conjunctions = filter(lambda f: isinstance(f, Conjunction), fs)
  disjunctions = filter(lambda f: isinstance(f, Disjunction), fs)

  return (literals, conjunctions, disjunctions)  # type: ignore


def simplify(f: Formula) -> Formula:
  if isinstance(f, bool) or isinstance(f, Intersect) or isinstance(
      f, IsContained):
    return f

  terms: FrozenSet[Formula]

  if isinstance(f, Conjunction):
    literals, conjunctions, disjunctions = split_by_type(
      filter(lambda term: term is not True, map(simplify, f.formulas)))

    terms = frozenset(
        chain(
            literals, disjunctions,
            chain.from_iterable(
                conjunction.formulas for conjunction in conjunctions)))

    # FIXME: We could check for subsumption among the predicates and disjunctions here.

    if not terms:
      return True
    elif len(terms) == 1:
      return next(iter(terms))
    elif False in terms:
      return False
    else:
      return Conjunction(terms)

  if isinstance(f, Disjunction):
    literals, conjunctions, disjunctions = split_by_type(
      filter(lambda term: term is not False, map(simplify, f.formulas)))

    terms = frozenset(
        chain(
            literals, conjunctions,
            chain.from_iterable(
                disjunction.formulas for disjunction in disjunctions)))

    # FIXME: We could check for subsumption among the predicates and conjunctions here.

    if not terms:
      return False
    elif len(terms) == 1:
      return next(iter(terms))
    elif True in terms:
      return True
    else:
      return Disjunction(terms)

  assert False


def _is_shallow(f: Union[Conjunction, Disjunction]) -> bool:
  return all(
      isinstance(formula, bool) or isinstance(formula, Intersect) or
      isinstance(formula, IsContained) for formula in f.formulas)


def CNF(f: Formula) -> Conjunction[Disjunction[Literal]]:
  f = simplify(f)
  if isinstance(f, bool) or isinstance(f, Intersect) or isinstance(
      f, IsContained):
    return Conjunction([Disjunction([f])])
  if isinstance(f, Conjunction):
    literals, _, disjunctions = split_by_type(f.formulas)
    cnfs = map(CNF,
      filter(lambda disjunction: not _is_shallow(disjunction), disjunctions))
    return Conjunction(chain(
      [Disjunction([literal]) for literal in literals],
      filter(_is_shallow, disjunctions),
      chain.from_iterable(cnf.formulas for cnf in cnfs)))
  if isinstance(f, Disjunction):
    # FIXME: See comment in DNF below.
    return Conjunction(map(Disjunction,
      product(*(conjunction.formulas for conjunction in DNF(f).formulas))))
  assert False


def DNF(f: Formula) -> Disjunction[Conjunction[Literal]]:
  f = simplify(f)
  if isinstance(f, bool) or isinstance(f, Intersect) or isinstance(
      f, IsContained):
    return Disjunction([Conjunction([f])])
  if isinstance(f, Disjunction):
    literals, conjunctions, _ = split_by_type(f.formulas)
    dnfs = map(DNF,
      filter(lambda conjunction: not _is_shallow(conjunction), conjunctions))
    return Disjunction(chain(
      [Conjunction([literal]) for literal in literals],
      filter(_is_shallow, conjunctions),
      chain.from_iterable(dnf.formulas for dnf in dnfs)))
  if isinstance(f, Conjunction):
    # FIXME: This is the simplest approach, but it does not work well in some cases. For
    # example: A ^ ((B ^ C) v (D ^ E) v (F ^ G)) should get transformed to simply
    # (A ^ B ^ C) v (A ^ D ^ E) v (A ^ F ^ G), but this approach will create a much longer,
    # messier expression.
    return Disjunction(map(Conjunction,
      product(*(disjunction.formulas for disjunction in CNF(f).formulas))))
  assert False


def term_is_computable(term: DocRegionTerm, fields: FrozenSet[Field]) -> bool:
  return term.field in fields


def is_computable(predicate: Predicate, fields: FrozenSet[Field]) -> bool:
  """Given the information of the document regions of these fields' assignments,
  can we compute the value of this predicate?"""
  return all(term_is_computable(term, fields) for term in predicate.terms)


def is_restrictor(
    predicate: Predicate, target_field: Field, fields: FrozenSet[Field]) -> bool:
  """Given the information of the document regions of these fields' assignments,
  does this predicate allow us to restrict the legal document regions of the
  target field's assignment?"""

  def is_naked_doc_region(term: DocRegionTerm) -> bool:
    return term.field == target_field and not term.transformation

  if isinstance(predicate, Intersect):
    return all(
        is_naked_doc_region(term) or term_is_computable(term, fields)
        for term in predicate.terms)
  if isinstance(predicate, IsContained):
    return (is_naked_doc_region(predicate.lhs) and term_is_computable(predicate.rhs, fields)) or \
            (term_is_computable(predicate.lhs, fields) and is_naked_doc_region(predicate.rhs))
  assert False


def weaken(f: Formula, field: Field, fields: FrozenSet[Field]) -> Formula:
  """Replace all non-restrictor terms in f with True.

  FIXME: This assumes our language does not have negation.
  """

  if isinstance(f, bool):
    return f
  if isinstance(f, Intersect) or isinstance(f, IsContained):
    return f if is_restrictor(f, field, fields) or is_computable(
        f, fields) else True
  if isinstance(f, Conjunction):
    return Conjunction(map(lambda g: weaken(g, field, fields), f.formulas))
  if isinstance(f, Disjunction):
    return Disjunction(map(lambda g: weaken(g, field, fields), f.formulas))
  assert False


def restrictive_power(
    f: Disjunction[Conjunction[Literal]], field: Field,
    fields: FrozenSet[Field]) -> float:

  def num_restrictors(conjunction: Conjunction[Literal]) -> int:
    return sum(
        1 for _ in filter(
            lambda g: not isinstance(g, bool) and is_restrictor(
                g, field, fields), conjunction.formulas))

  return max(map(num_restrictors, f.formulas))
