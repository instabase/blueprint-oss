import json

from dataclasses import asdict, dataclass
from functools import reduce
from itertools import chain
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..document import Document
from ..entity import Entity
from ..extraction import Extraction, Field
from ..rule import Atom, Predicate, Rule, RuleScore
from ..tree import Node


@dataclass
class WiifNode:
  node_uuid: str
  wiif_scores: Dict[str, RuleScore]
  child_nodes: List['WiifNode']
  uuid: str


def get_rule_scores(extraction: Extraction, node: Node, document: Document) \
    -> Dict[str, RuleScore]:

  def get_all_rules(N: Node) -> Tuple[Rule, ...]:
    return tuple(chain(N.rules,
      *(get_all_rules(child) for child in N.child_nodes or [])))
  def is_decidable(rule: Rule) -> bool:
    return extraction.fields.issuperset(frozenset(rule.fields))
  rule_scores = {rule.uuid: rule.with_document(document).rule_score(extraction)
    for rule in get_all_rules(node) if is_decidable(rule)}
  return rule_scores


def why_is_it_failing(
  extraction: Extraction, node: Node, document: Document) -> WiifNode:

  rule_scores = get_rule_scores(extraction, node, document)
  def build_wiif_tree(node: Node) -> WiifNode:
    node_rule_uuids = tuple(rule.uuid for rule in node.rules)
    node_wiif_scores = {uuid: score for uuid, score in rule_scores.items()
      if uuid in node_rule_uuids}
    return WiifNode(
      node.uuid,
      node_wiif_scores,
      list(build_wiif_tree(child) for child in node.child_nodes or []),
      str(uuid4()))
  return build_wiif_tree(node)


def save_wiif_node(wiif_node: WiifNode, path: Path) -> None:
  with path.open('w') as f:
    json.dump(asdict(wiif_node), f, indent=2, sort_keys=True)
