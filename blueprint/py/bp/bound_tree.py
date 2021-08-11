import logging

from dataclasses import dataclass, replace
from itertools import chain
from typing import Callable, Collection, Dict, FrozenSet, Iterator, List, Optional, Tuple, Union

from .bp_logging import bp_logging
from .doc_region_prefilter import DocRegionPrefilter
from .document import DocRegion, Document
from .entity import Entity
from .extraction import Extraction, Field
from .functional import arg_max, pairs
from .geometry import BBox, Interval
from .graphs import Graph
from .peeker import Peeker
from .peeking_heap import PeekingHeap
from .rule import Atom, Connective, Rule
from .scoring import ScoredExtraction, merge
from .smerger import Smerger
from .spatial_formula import Conjunction, DNF, Formula, restrictive_power, simplify, weaken
from .trivial_prefilter import TrivialPrefilter


@dataclass
class BoundNode(Iterator[ScoredExtraction]):

  def __init__(
      self,
      document: Document,
      legal_fields: FrozenSet[Field],
      rules: FrozenSet[Rule],
      name: str,
      uuid: str,
  ):
    self.document = document
    self.legal_fields = legal_fields
    self.rules = rules
    self.name = name
    self.uuid = uuid

    # Cached in _yielding.
    self.best_extraction: Optional[ScoredExtraction] = None
    self.returned_extractions: List[ScoredExtraction] = []

  def __next__(self) -> ScoredExtraction:
    raise NotImplementedError

  @property
  def mass(self) -> int:
    raise NotImplementedError

  @property
  def child_nodes(self) -> Tuple['BoundNode', ...]:
    """The direct child_nodes of this BoundNode."""
    raise NotImplementedError

  def is_decidable(self, rule: Rule) -> bool:
    """Can this rule be checked at this node?"""
    return frozenset(rule.fields) <= self.legal_fields

  def _yielding(self, extraction: ScoredExtraction) -> ScoredExtraction:
    if self.best_extraction is None or extraction < self.best_extraction:
      self.best_extraction = extraction
    self.returned_extractions.append(extraction)
    return extraction

  @property
  def num_extractions_generated(self) -> int:
    return len(self.returned_extractions)

  def __str__(self) -> str:
    return self.name


@dataclass
class BoundEmptyNode(BoundNode):

  def __init__(
      self,
      document: Document,
      name: str,
      uuid: str,
  ):
    super().__init__(document, frozenset(), frozenset(), name, uuid)

  def __next__(self) -> ScoredExtraction:
    raise StopIteration

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return tuple()


@dataclass
class BoundLeafNode(BoundNode):

  def __init__(
      self,
      document: Document,
      field: Field,
      rules: FrozenSet[Rule],
      name: str,
      uuid: str,
      extractions: Tuple[ScoredExtraction, ...],
  ):
    super().__init__(document, frozenset((field,)), rules, name, uuid)

    self.field = field
    self.extractions = extractions
    self.i = 0

  def __next__(self) -> ScoredExtraction:
    while self.i < len(self.extractions):
      # TODO: Non-Atom degree-1 rules should be accounted for at binding stage
      # already; once that's the case, pass no rules here.
      extraction = merge(
          [self.extractions[self.i]], frozenset(filter(
            lambda R: not isinstance(R, Atom), self.rules)), self.legal_fields,
          self.mass)
          # Degree-1 atom score results are cached -- the extractions passed to
          # BoundLeafNode's constructor should have these rules applied already.
      self.i += 1
      if extraction.valid:
        return self._yielding(self.extractions[self.i - 1])
      else:
        bp_logging.error(
            f'BoundLeafNode {self} was constructed with '
            f'an invalid extraction {extraction}')
    raise StopIteration

  @property
  def mass(self) -> int:
    return 1

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return tuple()


@dataclass
class BoundPatternNode(BoundNode):
  def __init__(
      self,
      document: Document,
      child: BoundNode,
      rules: FrozenSet[Rule],
      name: str,
      uuid: str,
  ):
    super().__init__(
      document, frozenset(filter(lambda F: len(F) > 0 and F[0] != '_',
        child.legal_fields)),
      rules, name, uuid)

    self.child = child

  def __next__(self) -> ScoredExtraction:
    # Keep private fields included in cached extractions so that they appear in
    # pattern results, but only pass along public fields to parents.
    return self.public_extraction(self._yielding(next(self.child)))

  @property
  def mass(self) -> int:
    return len(self.legal_fields)

  def public_extraction(self, scored_extraction: ScoredExtraction) \
      -> ScoredExtraction:
    extraction = Extraction(assignments=tuple(filter(
      lambda A: A.field in self.legal_fields,
      scored_extraction.extraction.assignments)))
    field_scores = {field: score
      for field, score in scored_extraction.field_scores.items()
      if field in self.legal_fields}
    return replace(scored_extraction,
      extraction=extraction, field_scores=field_scores)

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return (self.child,)


@dataclass
class BoundMergeNode(BoundNode):
  def __init__(
      self,
      document: Document,
      child: BoundNode,
      rules: FrozenSet[Rule],
      name: str,
      uuid: str,
  ):
    super().__init__(
      document, child.legal_fields, rules, name, uuid)

    self.child = child

  def __next__(self) -> ScoredExtraction:
    return self._yielding(next(self.child))

  @property
  def mass(self) -> int:
    return self.child.mass

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return (self.child,)


@dataclass
class BoundCombineNode(BoundNode):

  def __init__(
      self,
      document: Document,
      node1: BoundNode,
      node2: BoundNode,
      rules: FrozenSet[Rule],
      all_or_nothing: bool,
      name: str,
      uuid: str,
      peek_distance: int = 1,
  ):
    super().__init__(
      document, node1.legal_fields | node2.legal_fields,
      rules, name, uuid)

    self.node1 = node1
    self.node2 = node2

    decidable_atoms: Tuple[Atom, ...] = tuple(filter(
      lambda A: self.legal_fields.issuperset(A.fields),
      chain.from_iterable(map(
        lambda R: R.atoms if isinstance(R, Connective)
                          else (R,), rules))))

    # TODO: Should we include rules from lower in the hierarchy? Potential optimization.
    Phi = simplify(DNF(Conjunction(rule.phi for rule in decidable_atoms)))

    def prefilter_data(
        N_target: BoundNode,
        N_feeder: BoundNode) -> Tuple[Field, Formula]:

      def phi_I(field: Field) -> Formula:
        return simplify(weaken(Phi, field, N_feeder.legal_fields))

      I = arg_max(
          lambda I0: restrictive_power(
              DNF(phi_I(I0)), I0, N_feeder.legal_fields), N_target.legal_fields)

      return (I, phi_I(I))

    def prefilter(N_target: BoundNode, N_feeder: BoundNode) \
        -> Union[DocRegionPrefilter, TrivialPrefilter]:
      USE_DOC_REGION_PREFILTERING = True
      if N_target.legal_fields and N_feeder.legal_fields \
          and USE_DOC_REGION_PREFILTERING:
        return DocRegionPrefilter(*prefilter_data(N_target, N_feeder),
                                  self.document)
      else:
        return TrivialPrefilter()

    def merger(Ms: Tuple[ScoredExtraction, ...]) -> Optional[ScoredExtraction]:
      assert len(Ms) == 2
      M = merge(Ms, self.rules, self.legal_fields, self.mass)
      if all_or_nothing \
          and frozenset(M.fields) != self.legal_fields \
          and not M.is_empty:
        return None
      return M if M.valid else None

    def norm_estimator(Ms: Tuple[ScoredExtraction, ...]) -> float:
      return - sum(M.score * M.mass for M in Ms) \
              / sum(M.mass for M in Ms)

    def norm_getter(M: ScoredExtraction) -> float:
      return -M.score

    self.smerger = Smerger(
        ((node1, prefilter(node1, node2)), (node2, prefilter(node2, node1))),
        merger,
        norm_estimator,
        norm_getter,
        all_or_nothing=all_or_nothing,
        peek_distance=peek_distance,
        optimistic=True)

  def __next__(self) -> ScoredExtraction:
    return self._yielding(next(self.smerger))

  @property
  def mass(self) -> int:
    return sum(child.mass for child in self.child_nodes)

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return (self.node1, self.node2)


@dataclass
class BoundPickBestNode(BoundNode):

  def __init__(
      self,
      document: Document,
      child_nodes: Tuple[BoundNode, ...],
      rules: FrozenSet[Rule],
      name: str,
      uuid: str,
      peek_distance: int = 1,
  ):
    if not child_nodes:
      legal_fields: FrozenSet[Field] = frozenset()
    else:
      legal_fields = frozenset.union(
          *(child.legal_fields for child in child_nodes))
    super().__init__(document, legal_fields, rules, name, uuid)

    if peek_distance < 1:
      raise ValueError(
          f'PickBestNode peek_distance must be positive, not {peek_distance}')

    self.children = child_nodes
    self.heap = PeekingHeap(
      child_nodes,
      lambda S: S.normalize(self.mass),
      peek_distance=peek_distance)

  def __next__(self) -> ScoredExtraction:
    while True:
      M = merge([next(self.heap)], self.rules, self.legal_fields, self.mass)
      if M.valid:
        return self._yielding(M)

  @property
  def mass(self) -> int:
    return max(child.mass for child in self.child_nodes)

  @property
  def child_nodes(self) -> Tuple[BoundNode, ...]:
    return tuple(self.children)
