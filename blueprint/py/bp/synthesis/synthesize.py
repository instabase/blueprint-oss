from dataclasses import dataclass, replace
from functools import reduce
from itertools import chain, combinations
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple
from uuid import uuid4

from ..synthesis.rules import SynthesizedRules, find_rules_for_extraction, text_equals
from ..synthesis.targets import generate_target_extraction, get_target_spatial_info_for_all_docs, get_target_spatial_info_for_doc

from ..document import Document
from ..extraction import Extraction, ExtractionPoint, Field
from ..geometry import BBox, Interval
from ..model import validate
from ..functional import adjacent_pairs, arg_max, arg_min
from ..graphs import components
from ..rule import Atom, Predicate, Rule, RuleScore
from ..targets import DocTargets, TargetValue, Targets, TargetsSchema, get_labels_from_schema, schema_type_map, validate_extraction
from ..tree import Node, PatternNode, PickBestNode

from ..rules.textual import TextEquals


# PARAMETERS #
number_of_nodes: Callable[[Tuple[PatternNode, ...]], int] = lambda R: len(R)
min_fields: Callable[[List[Field]], int] = lambda F: len(F)
generalize_text_equals = False
min_spatial_matches = 1


def synthesize_pattern_node(
  extraction: Extraction,
  schema: TargetsSchema,
  document: Document) -> Node:
  extraction = validate_extraction(extraction, schema)
  synthesized_rules = find_rules_for_extraction(extraction, schema, document)
  type_map = {point.field: point.entity.type for point in extraction.assignments}
  return validate(PatternNode(
    rules=synthesized_rules.rules,
    fields=type_map))


# For Wizard
def synthesize_node_from_targets(
  targets: Targets,
  documents: List[Document],
  fields: List[Field]) -> Tuple[Node, Dict[str, DocTargets]]:

  labels = get_labels_from_schema(targets.schema)
  targets_by_doc = get_target_spatial_info_for_all_docs(
    targets, documents, fields)

  pattern_nodes = get_pattern_nodes_from_target_sets(
    targets_by_doc, targets.schema, fields)
  if len(pattern_nodes) == 0:
    raise RuntimeError('No rule sets found')
  node_count = number_of_nodes(pattern_nodes)
  # FIXME: Add weight to templates with less fields instead of this.
  pattern_nodes = tuple(filter(
    lambda R: len(R.fields) >= min_fields(fields), pattern_nodes))
  # Nodes are sorted in decreasing order of how many targets they match
  if generalize_text_equals:
    pattern_nodes = generalize_textual_rules(pattern_nodes)
  nodes = tuple(pattern_nodes[:node_count])
  root = validate(PickBestNode(children=nodes))

  targets_by_doc_name = {doc.name or '': targets
    for doc, targets in targets_by_doc.items()}

  return (root, targets_by_doc_name)


def get_pattern_nodes_from_target_sets(
  targets_by_doc: Dict[Document, DocTargets],
  schema: TargetsSchema,
  fields: List[Field]) -> Tuple[PatternNode, ...]:

  spatial_groups: Dict[Tuple[Rule, ...], List[SynthesizedRules]] = {}

  for document, targets in targets_by_doc.items():
    extraction = generate_target_extraction(targets, schema, document)
    if extraction is None:
      continue
    synthesized_rules = find_rules_for_extraction(extraction, schema, document)
    if synthesized_rules.spatial in spatial_groups:
      spatial_groups[synthesized_rules.spatial] += [synthesized_rules]
    else:
      spatial_groups[synthesized_rules.spatial] = [synthesized_rules]

  def create_node(rule_sets: List[SynthesizedRules]) -> PatternNode:
    assert len(rule_sets) > 0
    # All sets should have same spatial rules
    spatial_rules = rule_sets[0].spatial
    textual_rules = chain.from_iterable(rule_set.textual
      for rule_set in rule_sets)
    # FIXME: Choose these by majority.
    type_rules = rule_sets[0].type

    field_text_options: Dict[Field, FrozenSet[str]] = {}
    for rule in textual_rules:
      assert isinstance(rule, Atom) \
        and isinstance(rule.predicate, TextEquals) \
        and len(rule.fields) == 1
      field = rule.fields[0]
      arg = frozenset(rule.predicate.texts)
      field_text_options[field] = field_text_options[field] | arg \
        if field in field_text_options else arg

    generalized_textual_rules = tuple(Atom(fields=(field,),
        predicate=TextEquals(tuple(field_text_options[field])))
      for field in frozenset(field_text_options.keys()))

    rules = tuple(chain(spatial_rules, generalized_textual_rules, type_rules))
    fields = frozenset(tuple(chain.from_iterable(rule.fields
      for rule in rules)))
    labels = get_labels_from_schema(schema)
    node_labels = list(filter(lambda F: F in labels, fields))
    type_map = schema_type_map(schema)
    validated_node = validate(
      PatternNode(
        rules=rules,
        fields={field: type_map[field] for field in fields}))
    assert isinstance(validated_node, PatternNode)
    return validated_node

  def valid_group(group: List[SynthesizedRules]) -> bool:
    return len(group) >= min_spatial_matches
  return tuple(create_node(rule_sets)
    for rule_sets in filter(valid_group, spatial_groups.values()))


def generalize_textual_rules(nodes: Tuple[PatternNode, ...]) \
    -> Tuple[PatternNode, ...]:
  def is_textual_rule(rule: Rule) -> bool:
    return isinstance(rule, Atom) and rule.predicate.name == 'text_equals'
  textual_rules = tuple(filter(is_textual_rule,
    chain.from_iterable(node.rules for node in nodes)))

  field_text_options: Dict[Field, FrozenSet[str]] = {}
  for rule in textual_rules:
    assert isinstance(rule, Atom) \
        and len(rule.fields) == 1 \
        and isinstance(rule.predicate, TextEquals)
    field = rule.fields[0]
    arg = frozenset(rule.predicate.texts)
    field_text_options[field] = field_text_options[field] | arg \
      if field in field_text_options else arg
  def get_textual_rules_for_node(node: PatternNode) -> Tuple[Rule, ...]:
    return tuple(Atom(
        fields=(field,),
        predicate=TextEquals(tuple(field_text_options[field])))
      for field in frozenset(field_text_options.keys())
      & frozenset(node.fields or []))

  nodes = tuple(replace(node,
    rules=tuple(filter(lambda R: not is_textual_rule(R),
    node.rules)) + get_textual_rules_for_node(node)) for node in nodes)
  return nodes
