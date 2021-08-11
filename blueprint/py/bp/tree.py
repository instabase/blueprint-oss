"""Extraction tree.

You can think of an extraction tree as a hierarchical description of a
document's structure. For example, you might have a node describing the header,
another for the body, and another for the footer. These nodes will themselves be
made up of subnodes describing parts of the document lower in the hierarchy,
such as key-value pairs, checkboxes, tables, table rows, and so on.

Each node of an extraction tree has fields it is responsible for, and rules
describing the extraction we want. An extraction tree can be bound to a
document, resulting in an iterator that returns extractions, an extraction being
a simultaneous assignment for each field to some entity in the document.

The idea is that the nodes should be smart-enough to return higher-quality
extractions first. That way, to find good extractions, a node can examine just
the first few examples from each of its child_nodes, and combine them in the way
that makes the most sense at its level in the hierarchy. The last extraction
that each node returns is the empty extraction.

The reason we need to examine multiple extractions is that an assignment for a
field can look good at a low level, but end up not making sense at a higher
level. For example, determining whether a certain word is part of a table row
may require us to look at the table heading. On the other hand, determining
whether some other word is part of the *heading* may require us to examine how
well the things underneath it fit as part of our table's rows. The
multiple-drafts approach allows this logic to naturally apply in both
directions. As another example, detecting and correcting (low-level) OCR errors
may require (high-level) contextual understanding, which in turn depends on the
OCR.
"""

import dataclasses
import logging

from functools import lru_cache, reduce
from itertools import chain, product
from typing import Any, Collection, Dict, FrozenSet, Generator, Iterable, List, Optional, Sequence, Tuple, Union
from uuid import UUID, uuid4

from .bound_tree import BoundCombineNode, BoundEmptyNode, BoundLeafNode, BoundMergeNode, BoundNode, BoundPatternNode, BoundPickBestNode
from .bp_logging import bp_logging
from .document import Document
from .entity import Entity, Page
from .extraction import Assignment, Extraction, ExtractionPoint, Field, MissingFieldsError, OverlappingFieldsError, UnrecognizedFieldsError
from .functional import adjacent_pairs, all_equal, comma_sep, disj, negate, nonempty, pairs, pairwise_disjoint
from .geometry import BBox
from .graphs import Component, Graph, WeightedMultiGraph, components as graph_components
from .rule import Atom, RuleScore, Conjunction, Connective, Degree1Predicate, Disjunction, Predicate, Rule, get_atoms
from .scoring import ScoredExtraction, assignment_is_valid, extraction_score, leaf_score

from .rules.logical import AreDisjoint
from .rules.semantic import IsDate, IsDollarAmount, IsEntirePhrase


@dataclasses.dataclass(frozen=True)
class _CachedScoredAssignment:
  assignment: Assignment
  field_score: float
  rule_scores: Dict[Predicate, RuleScore]

  def is_valid(self) -> bool:
    return assignment_is_valid(self.assignment, self.field_score)

  def __lt__(self, other: '_CachedScoredAssignment') -> bool:
    return self.field_score > other.field_score


@lru_cache(maxsize=None)
def assignments(
  document: Document,
  predicates: FrozenSet[Predicate],
  type: str) -> Tuple[_CachedScoredAssignment, ...]:
  """The assignments of some unspecified field, along with the resulting field
  scores, in sorted order according to how well these rules are satisfied.

  This excludes assignments which are invalid, as defined by the function
  assignment_is_valid.

  Args:
    document: The document from which to draw assignments. An assignment to None
      will always be included.
    predicates: The predicates to use to calculate field scores. Note that no
      field is present: multiple fields may be subject to the same set of
      predicates, and by omitting the field we can memoize this computation.
    type: The type required for Entities assigned to this field.

  Returns:
    The possible assignments of a field, their associated field scores, and
    their associated rule scores.
  """

  assignments: Tuple[Assignment, ...] = (*filter(
    lambda E: E.type == type, document.entities), None)
  CSAs = (_CachedScoredAssignment(E, *leaf_score(E, predicates, document))
    for E in assignments)
  return tuple(sorted(filter(_CachedScoredAssignment.is_valid, CSAs)))


@dataclasses.dataclass(frozen=True)
class Node:
  """A node in an extraction tree."""

  rules: Tuple[Rule, ...]
  uuid: str
  name: Optional[str]
  type: str

  def validate(self) -> None:
    for rule in self.rules:
      if not frozenset(rule.fields) <= self.legal_fields:
        raise UnrecognizedFieldsError(
            f'rule {rule} refers to '
            f'fields {frozenset(rule.fields) - self.legal_fields} '
            f'not found in {self}')

  def bound_to(self, document: Document) -> BoundNode:
    raise NotImplementedError

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    """The fields which may be present in extractions this node generates."""
    raise NotImplementedError

  @property
  def child_nodes(self) -> Tuple['Node', ...]:
    """The immediate child_nodes of this Node in the extraction tree."""
    raise NotImplementedError

  def is_decidable(self, rule: Rule) -> bool:
    """Can this rule be checked at this node?"""
    return frozenset(rule.fields) <= self.legal_fields

  def all_rules(self) -> Generator[Rule, None, None]:
    """Yields the rules at this node and all descendant nodes."""
    yield from self.rules
    for child in self.child_nodes:
      yield from child.all_rules()

  def with_name(self, name: str) -> 'Node':
    """Remake this Node, with the given name."""
    return dataclasses.replace(self, name=name)

  def with_uuid(self, uuid: Optional[str]) -> 'Node':
    """Remake this Node, with the given uuid."""
    return dataclasses.replace(self, uuid=uuid)

  def with_extra_rules(self, *rules: Rule) -> 'Node':
    """Remake this Node, adding the given rules.

    These rules will be added to any rules already present at the node.
    """
    return self.with_rules(tuple(chain(self.rules, rules)))

  def with_rules(self, rules: Tuple[Rule, ...]) -> 'Node':
    """Remake this Node, replacing any rules that were present with these
    rules."""
    return dataclasses.replace(self, rules=rules)


@dataclasses.dataclass(frozen=True)
class EmptyNode(Node):
  """A Node with no fields or rules."""

  def __init__(
    self,
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'empty',
  ) -> None:
    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'empty':
      raise ValueError('type mismatch building EmptyNode')
    object.__setattr__(self, 'type', type)

  def __post_init__(self) -> None:
    if self.rules:
      raise ValueError(f'EmptyNode rules must be empty, not {self.rules}')

  def bound_to(self, document: Document) -> BoundEmptyNode:
    return BoundEmptyNode(document, str(self), uuid=self.uuid)

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    return frozenset()

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return tuple()

  def __str__(self) -> str:
    return self.name or 'EmptyNode()'


@dataclasses.dataclass(frozen=True)
class LeafNode(Node):
  """A leaf in an extraction tree.

  Bind this to a document to generate assignments from the field to entities in
  the document, satisfying the rules.
  """

  field: Field
  entity_type: str

  def __init__(
    self,
    field: Field,
    entity_type: str,
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'leaf',
  ):
    object.__setattr__(self, 'field', field)
    object.__setattr__(self, 'entity_type', entity_type)
    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'leaf':
      raise ValueError('type mismatch building LeafNode')
    object.__setattr__(self, 'type', type)

  def bound_to(self, document: Document) -> BoundLeafNode:

    def scored_extraction(CSA: _CachedScoredAssignment) -> ScoredExtraction:
      extraction = Extraction((ExtractionPoint(self.field, CSA.assignment),)) \
        if CSA.assignment else Extraction(tuple())
      rule_scores = {Atom((self.field, ), predicate, str(uuid4())): rule_score
        for predicate, rule_score in CSA.rule_scores.items()}
      field_scores = {self.field: CSA.field_score}
      return ScoredExtraction(
          extraction=extraction,
          score=extraction_score(field_scores, mass=1),
          field_scores=field_scores,
          rule_scores={
            rule_uuids[rule]: rule_score
                for rule, rule_score in rule_scores.items()
          },
          mass=1,
      )

    rule_uuids = {rule: rule.uuid for rule in self.rules}
    # FIXME: Really need to look at non-Atom rules here too.
    CSAs = assignments(document, frozenset(rule.predicate
      for rule in self.rules if isinstance(rule, Atom)), self.entity_type)
    scored_extractions = tuple(map(scored_extraction, CSAs))
    # Empty extraction must be returned last for Smerger all_or_nothing logic.
    assert len(scored_extractions) > 0 and scored_extractions[-1].is_empty
    return BoundLeafNode(
        document,
        self.field,
        frozenset(rule.with_document(document)
          for rule in self.rules),
        name=self.name or str(self),
        uuid=self.uuid,
        extractions=scored_extractions,
    )

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    return frozenset({self.field})

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return tuple()

  def __str__(self) -> str:
    return self.name or f'LeafNode({self.field})'


@dataclasses.dataclass(frozen=True)
class PatternNode(Node):
  """A node whose tree structure is reconstructed for each document.

  See the documentation for order_tree below for tree ordering details.
  """

  fields: Dict[Field, str]

  def __init__(
    self,
    fields: Dict[Field, str],
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'pattern',
  ):
    object.__setattr__(self, 'fields', fields)
    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'pattern':
      raise ValueError('type mismatch building PatternNode')
    object.__setattr__(self, 'type', type)

  def bound_to(self, document: Document) -> BoundNode:
    def order_tree() -> Node:
      """Create a new tree structure for each document.

      The fields bound to the node's rules are grouped into components, such
      that for any two components A and B, there is no rule R such that R is
      bound to field 'a' in A and field 'b' in B.

      Within these components, the fields are each assigned an estimate of how many
      possible values they have at a leaf node level, and each rule is assigned an
      estimate of how many assignments it will eliminate. This way, the expected 
      number of possible assignments a combine node has can be loosely approximated 
      as the the expected possibilities of its children multiplied together reduced by
      the expected reduction of any rules that connect them.

      Iteratively, the pair of nodes with the least expected assignments are removed 
      from consideration and bound into a combine node. This process repeats until only 
      a single node remains, serving as the root for the tree of that component.

      This structure is not guaranteed to be optimal.
      """

      def build_leaf_node(field: Field) -> LeafNode:
        leaf_rules = tuple(filter(
            lambda p: frozenset((field,)) == frozenset(p.fields), self.rules))
        result = LeafNode(field, self.fields[field]).with_rules(leaf_rules)
        assert isinstance(result, LeafNode)
        return result

      fields = self.legal_fields
      leaf_nodes: Iterable[LeafNode] = map(build_leaf_node, fields)
      bound_leaf_nodes = (leaf_node.bound_to(document)
        for leaf_node in leaf_nodes)

      num_leaf_assignments: Dict[Field, int] = {
          bound_leaf_node.field: len(bound_leaf_node.extractions)
          for bound_leaf_node in bound_leaf_nodes}

      rules = tuple(chain.from_iterable(map(
        lambda R: R.atoms if isinstance(R, Connective) else (R,), self.rules)))

      field_components: FrozenSet[Component[Field]] = graph_components(
          (rule.fields for rule in rules))
      component_graphs: Tuple[WeightedMultiGraph, ...] = tuple()

      def build_weighted_graph(component: Component[Field]) \
          -> WeightedMultiGraph[Field]:
        component_rules = filter(
          lambda p: component.issuperset(p.fields), rules)
        GraphEdge = Tuple[Field, Field]
        edge_list: List[GraphEdge] = []
        weights: Dict[GraphEdge,Tuple[float, ...]] = {}
        for rule in component_rules:
          assert(isinstance(rule, Atom))
          if len(rule.fields) == 1:
            v1 = rule.fields[0]
            edge = (v1, v1)
          elif len(rule.fields) == 2:
            v1, v2 = (field for field in rule.fields)
            edge = (v1, v2) if v1 < v2 else (v2, v1)
          else:
            # We currently don't have any base predicates (excluding
            # any_holds, all_hold) that can be bound to more than two fields.
            continue
          edge_list.append(edge)
          weights[edge] = weights[edge] + (rule.predicate.leniency(),) \
            if edge in weights else (rule.predicate.leniency(),)
        return WeightedMultiGraph(
          vertices=frozenset(component),
          edges=frozenset(edge_list),
          weights=weights
        )

      for component in field_components:
        assert len(component) > 0
        wgraph = build_weighted_graph(component)
        component_graphs += (wgraph,)

      def estimated_valid_assignments(
        wgraph: WeightedMultiGraph[Field]
      ) -> float:
        approx_combined_leniency = 1.0
        for edge, edge_weights in wgraph.weights.items():
          for weight in edge_weights:
            approx_combined_leniency *= weight
        approx_total_possible_assignments = 1.0
        for field in wgraph.vertices:
          approx_total_possible_assignments *= num_leaf_assignments[field]
        return approx_total_possible_assignments * approx_combined_leniency


      def graph_order_key(wgraph: WeightedMultiGraph[Field]) -> float:
        assert isinstance(wgraph, WeightedMultiGraph)
        assert len(wgraph.vertices) > 0
        return estimated_valid_assignments(wgraph)

      ordered_graphs = tuple(
          sorted(component_graphs, key=graph_order_key))
      ordered_trees = map(
        lambda g: build_tree_from_graph(
          g, self.fields, num_leaf_assignments), ordered_graphs)
      root = reduce(
        lambda L1, L2: combine(
        L1, L2, all_or_nothing=True), ordered_trees)
      return _validated(distribute_rules(root, rules))
    return BoundPatternNode(
      document=document,
      child=order_tree().bound_to(document),
      rules=frozenset(self.rules),
      name=self.name or str(self),
      uuid=self.uuid)

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    return frozenset(self.fields)

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return tuple()

  def __str__(self) -> str:
    return self.name or f'PatternNode({comma_sep(self.legal_fields)})'


@dataclasses.dataclass(frozen=True)
class MergeNode(Node):
  """Merge the outputs of several extraction nodes."""

  children: Tuple[Node, ...]

  def __init__(
    self,
    children: Tuple[Node, ...],
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'merge',
  ):
    object.__setattr__(self, 'children', children)
    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'merge':
      raise ValueError('type mismatch building MergeNode')
    object.__setattr__(self, 'type', type)

  def validate(self) -> None:
    super().validate()
    if not pairwise_disjoint(child.legal_fields for child in self.children):
      raise OverlappingFieldsError(
        f'some fields appear in multiple children')

  def bound_to(self, document: Document) -> BoundMergeNode:
    return BoundMergeNode(
      document=document,
      child=combine(*self.children).bound_to(document),
      rules=frozenset(self.rules),
      name=self.name or str(self),
      uuid=self.uuid)

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    return frozenset(chain.from_iterable(child.legal_fields
      for child in self.children))

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return tuple(self.children)

  def __str__(self) -> str:
    return self.name or f'MergeNode({comma_sep(self.legal_fields)})'


@dataclasses.dataclass(frozen=True)
class CombineNode(Node):
  """Combine the outputs of two extraction nodes.

  Given two extraction nodes for distinct parts of a document, this takes
  extractions from each node and combines them, possibly applying some
  additional rules, and returns the resulting higher-level extractions, roughly
  in best-to-worst order.

  Attributes:
    node1: An extraction tree node.
    node2: Another extraction tree node, whose extractions' fields are different
      from those of node1.
    all_or_nothing: If True, all fields are required. Defaults to False.
    peek_distance: How far along the two subtrees to peek ahead in the
      underlying smerger. At least 2 is recommended (the default value).
  """

  node1: Node
  node2: Node
  all_or_nothing: bool
  peek_distance: int

  def __init__(
    self,
    node1: Node,
    node2: Node,
    all_or_nothing: bool = False,
    peek_distance: int = 2,
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'combine',
  ):
    object.__setattr__(self, 'node1', node1)
    object.__setattr__(self, 'node2', node2)
    object.__setattr__(self, 'all_or_nothing', all_or_nothing)
    object.__setattr__(self, 'peek_distance', peek_distance)

    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'combine':
      raise ValueError('type mismatch building CombineNode')
    object.__setattr__(self, 'type', type)

  def validate(self) -> None:
    super().validate()
    union = self.node1.legal_fields & self.node2.legal_fields
    if union:
      raise OverlappingFieldsError(
          f'fields {union} appear in both {self.node1} and {self.node2}')
    if self.peek_distance < 1:
      raise ValueError(
          f'Combine node peek distance must be positive, '
          f'but {self} was given {self.peek_distance}')
    if self.peek_distance == 1:
      bp_logging.warning(
          f'Peek distance of 1 in {self} '
          f'may result in poor performance')

  def bound_to(self, document: Document) -> BoundCombineNode:
    return BoundCombineNode(
        document,
        self.node1.bound_to(document),
        self.node2.bound_to(document),
        frozenset(rule.with_document(document)
          for rule in self.rules),
        all_or_nothing=self.all_or_nothing,
        name=self.name or str(self),
        uuid=self.uuid,
        peek_distance=self.peek_distance,
    )

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    return self.node1.legal_fields | self.node2.legal_fields

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return (self.node1, self.node2)

  def __str__(self) -> str:
    return self.name or f'CombineNode({comma_sep(self.legal_fields)})'


@dataclasses.dataclass(frozen=True)
class PickBestNode(Node):
  """An extraction selector.

  This is for picking the best extractions from one of several extraction
  subtrees. This is used when a document can have different layouts or
  sublayouts, so we define separate extraction trees corresponding to the
  different layouts. Then we want to use the best extraction we find from any of
  the layouts: that's what PickBestNode is for.
  """

  children: Tuple[Node, ...]

  def __init__(
    self,
    children: Tuple[Node, ...],
    rules: Tuple[Rule, ...] = tuple(),
    uuid: Optional[str] = None,
    name: Optional[str] = None,
    type: str = 'pick_best',
  ):
    object.__setattr__(self, 'children', children)

    object.__setattr__(self, 'rules', rules)
    object.__setattr__(self, 'uuid', uuid if uuid is not None else str(uuid4()))
    object.__setattr__(self, 'name', name)

    if type != 'pick_best':
      raise ValueError('type mismatch building PickBestNode')
    object.__setattr__(self, 'type', type)

  def bound_to(self, document: Document) -> BoundPickBestNode:
    return BoundPickBestNode(
        document,
        child_nodes=tuple(child.bound_to(document)
          for child in self.child_nodes),
        rules=frozenset(rule.with_document(document)
          for rule in self.rules),
        name=self.name or str(self),
        uuid=self.uuid,
    )

  @property
  def legal_fields(self) -> FrozenSet[Field]:
    if not self.child_nodes:
      return frozenset()
    return frozenset.union(*(child.legal_fields for child in self.children))

  @property
  def child_nodes(self) -> Tuple[Node, ...]:
    return tuple(self.children)

  def __str__(self) -> str:
    return self.name or f'PickBestNode({comma_sep(self.child_nodes)})'


def _validated(node: Node) -> Node:
  node.validate()
  return node


def _validated_overlappable_pairs(pairs: Iterable[Iterable[Field]]) \
    -> FrozenSet[FrozenSet[Field]]:
  allowed_to_overlap: FrozenSet[FrozenSet[Field]] = \
    frozenset(map(frozenset, pairs))
  for pair in allowed_to_overlap:
    if len(pair) != 2 or not all(isinstance(entry, Field) for entry in pair):
      raise ValueError(
        f'allowed_to_overlap entries must be pairs of fields, not {pair}')
  return allowed_to_overlap


def extract(*rules: Rule, field_types: Optional[Dict[Field, str]] = None) \
    -> Node:
  """Find an extraction satisfying the given rules.

  This is the most basic extraction building block. If there is a lot of
  branching in document structure, you will probably need to use combine and/or
  pick_best, both defined below.

  The returned extractions will have non-None values for every field bound to
  the rules, unless the field is optional or is the first field in a dependency
  pair.

  Args:
    rules: The rules you want your extraction to satisfy. The order of these
      does not matter. The fields that will be extracted are those bound to
      these rules.
    field_types: An optional dictionary from Field to Entity type. If this is
      not provided, field types will be determined automatically based upon
      the presence of predicates IsDate, IsDollarAmount, and IsEntirePhrase.
      Only Entity types Date, DollarAmount, and Text are determined
      automatically.
  """

  if field_types is None:
    fields = frozenset(chain.from_iterable(rule.fields for rule in rules))
    atoms = tuple(rule for rule in rules if isinstance(rule, Atom))

    def has_type_rule(field: Field, predicate_type: type) -> bool:
      return any(isinstance(atom.predicate, predicate_type)
                  and atom.fields == (field,) for atom in atoms)

    dates = frozenset(filter(lambda F: has_type_rule(F, IsDate), fields))
    dollar_amounts = frozenset(filter(
      lambda F: has_type_rule(F, IsDollarAmount), fields))
    phrases = frozenset(filter(
      lambda F: has_type_rule(F, IsEntirePhrase), fields))

    if frozenset.intersection(dates, dollar_amounts, phrases):
      raise TypeError(
        f'fields {frozenset.intersection(dates, dollar_amounts, phrases)} '
        'cannot be multiple types. Fields should be applied to maximum 1 out '
        'of predicates `is_date`, `is_dollar_amount`, `is_entire_phrase`')

    # Currently supported types: Date, DollarAmount, Text. See entity.py for
    # for other potential Entity types to add in the future as desired.
    def get_field_type(field: Field) -> str:
      if field in dates:
        return 'Date'
      if field in dollar_amounts:
        return 'DollarAmount'
      return 'Text'

    field_types = {field: get_field_type(field) for field in fields}

  rules_ = tuple(rules)
  for rule in rules_:
    # Sanity-checking rule
    hash(rule)

  return PatternNode(
      rules=rules_,
      name=None,
      fields=field_types,
  )


def combine(*nodes: Node,
            all_or_nothing: bool = False,
            allowed_to_overlap: Iterable[Iterable[Field]]=tuple()) -> Node:
  """Combine several extraction trees.

  Given extraction trees for separate parts of the document, combine them into
  one bigger extraction. The fields in the subtrees have to be distinct.
  By default, this adds rules that say that the entities assigned to fields from
  different subtrees do not overlap. You can override this behavior with
  allowed_to_overlap.

  Warning: The order in which these are given can have a big impact on runtime.

  Args:
    nodes: Extraction trees.
    all_or_nothing: If True, if any fields are not able to be extracted, none
      will be.
    allowed_to_overlap: Pairs of fields whose assigned entities are allowed to
      overlap. For each such pair (f1, f2), it is required that f1 and f2 come
      from different nodes.

  Examples:
    If you have subtree_1 and subtree_2, which contain fields 'label_1' and
    'label_2' respectively, which may in some cases refer to the same actual
    entity in the document, you would call:

      combine(
        subtree_1,
        subtree_2,
        allowed_to_overlap=[
          ['label_1', 'label_2']
        ])
  """
  if len(nodes) == 0:
    return EmptyNode()
  allowed_to_overlap_ = _validated_overlappable_pairs(allowed_to_overlap)
  rules = chain.from_iterable(
    (Atom(fields=(field1, field2),
          predicate=AreDisjoint(),
          uuid=str(uuid4()))
      for field1, field2 in product(node1.legal_fields, node2.legal_fields)
      if frozenset({field1, field2}) not in allowed_to_overlap_)
    for node1, node2 in pairs(nodes))
  return _validated(reduce(
    lambda N1, N2: CombineNode(N1, N2, all_or_nothing), nodes) \
        .with_extra_rules(*rules))


def pick_best(*nodes: Node) -> Node:
  """Use the best extractions from a collection.

  Given multiple extraction trees for the same part of a document (for example,
  multiple templates), use the ones that perform the best.

  Args:
    nodes: Some extraction trees.
  """
  return _validated(PickBestNode(nodes))


def build_tree_from_graph(
  graph: WeightedMultiGraph[Field],
  field_types: Dict[Field, str],
  num_leaf_assignments: Dict[Field, int]
) -> Node:
  assert len(graph.vertices) > 0
  GraphEdge = Tuple[Field, Field]

  def build_leaf_node(field: Field) -> Node:
    return LeafNode(field, field_types[field])
  
  def product_weight(edge: GraphEdge) -> float:
    product = 1.0
    for weight in graph.weights[edge]:
      product *= weight
    return product

  node_associations: Dict[Field, Node] = {
    v: build_leaf_node(v) for v in graph.vertices
  }
  vertex_weights: Dict[Field, float] = {
    v: num_leaf_assignments[v]*(
      product_weight((v, v)) if (v, v) in graph.edges\
      else 1)
    for v in graph.vertices}

  def edge_key(edge: GraphEdge) -> float:
    return vertex_weights[edge[0]]*vertex_weights[edge[1]]*product_weight(edge)

  while len(graph.vertices) > 1:
    best_edge=min([e for e in graph.edges if e[0] != e[1]], key=edge_key)
    weight = edge_key(best_edge)
    new_node = combine(node_associations[best_edge[0]],
      node_associations[best_edge[1]],
      all_or_nothing=True)
    node_associations[best_edge[0]] = new_node
    vertex_weights[best_edge[0]] = weight
    graph = graph.with_vertices_collapsed(
      old_vertices=frozenset(best_edge),
      new_vertex=best_edge[0])

  return node_associations[next(iter(graph.vertices))]
  

def distribute_rules(node: Node, rules: Tuple[Rule, ...]) -> Node:
  """Distribute the rules in a CombineNode extraction subtree.

  We do not mutate the input tree. The returned tree will be deep-copied as
  needed.

  Args:
    node: An extraction tree node. This node and its descendants should all be
      of type CombineNode or LeafNode.
    rules: Rules to add to the tree.
  """

  rules = tuple(chain(rules, node.rules))

  if isinstance(node, CombineNode):
    def remake_combine_node_child(child: Node) -> Node:
      def has_decidable_atom(rule: Rule) -> bool:
        return len(tuple(filter(
          lambda A: child.is_decidable(A), get_atoms(rule)))) != 0
      child_rules = tuple(filter(lambda R: has_decidable_atom(R), rules))
      return distribute_rules(child, child_rules)

    # "Spanning" means that the rule/component involves fields from both of the
    # CombineNode's child_nodes.
    spanning_rules = tuple(filter(
      negate(disj([
        node.node1.is_decidable,
        node.node2.is_decidable])),
      rules))

    return dataclasses.replace(
      node,
      node1=remake_combine_node_child(node.node1),
      node2=remake_combine_node_child(node.node2),
      rules=spanning_rules)

  else:
    assert isinstance(node, LeafNode)
    return node.with_rules(rules)
