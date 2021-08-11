#!/usr/bin/env python3

"""Blueprint model serialization."""

import json

from dataclasses import asdict, dataclass, field as dc_field, replace
from pathlib import Path
from sys import argv
from typing import Any, Dict, List, Optional, Set, Type, Union
from uuid import UUID

from .entity import Entity
from .instantiate import instantiate
from .rule import Atom, Conjunction, Connective, Disjunction, Predicate, Rule
from .rules.impingement import NoWordsBetweenHorizontally, NoWordsBetweenVertically, NothingBetweenHorizontally, NothingBetweenVertically
from .rules.semantic import IsAddress, IsDate, IsDollarAmount, IsEntirePhrase, IsPersonName
from .rules.spatial import BottomAligned, LeftAligned, LeftToRight, RightAligned, TopDown, AreOnSamePage
from .rules.textual import TextEquals
from .tree import Node, MergeNode, PickBestNode, PatternNode


BlueprintModel = Node
NodeWithChildren = Union[MergeNode, PickBestNode]


def validate_rule(rule: Rule, node: Node) -> Rule:
  UUID(rule.uuid)

  atoms = rule.atoms if isinstance(rule, Connective) else frozenset({rule})
  for atom in atoms:
    if len(frozenset(atom.fields)) != len(atom.fields):
      raise ValueError(
        f'rule {(rule.uuid)} cannot have '
        f'repeated fields {atom.fields}')

  for field in rule.fields:
    if field not in node.legal_fields:
      raise ValueError(
        f'unrecognized field {field} '
        f'in rule {rule.uuid}')

  return rule


def validate(node: Node) -> Node:
  UUID(node.uuid)

  if isinstance(node, MergeNode) or isinstance(node, PickBestNode):
    for child in node.child_nodes:
      validate(child)

  for rule in node.rules:
    validate_rule(rule, node)

  return node


def load_model_from_json(blob: Dict) -> BlueprintModel:

  def derived_class_resolver(v: Any) -> Type:
    assert isinstance(v, dict)

    if 'type' in v:

      if v['type'] == 'pattern':
        return PatternNode

      if v['type'] == 'merge':
        return MergeNode

      if v['type'] == 'pick_best':
        return PickBestNode

      if v['type'] == 'atom':
        return Atom

      if v['type'] == 'conjunction':
        return Conjunction

      if v['type'] == 'disjunction':
        return Disjunction

    if 'name' in v:

      if v['name'] == 'text_equals':
        return TextEquals

      if v['name'] == 'bottom_aligned':
        return BottomAligned

      if v['name'] == 'left_aligned':
        return LeftAligned

      if v['name'] == 'right_aligned':
        return RightAligned

      if v['name'] == 'left_to_right':
        return LeftToRight

      if v['name'] == 'top_down':
        return TopDown

      if v['name'] == 'are_on_same_page':
        return AreOnSamePage

      if v['name'] == 'nothing_between_horizontally':
        return NothingBetweenHorizontally

      if v['name'] == 'nothing_between_vertically':
        return NothingBetweenVertically

      if v['name'] == 'no_words_between_horizontally':
        return NoWordsBetweenHorizontally

      if v['name'] == 'no_words_between_vertically':
        return NoWordsBetweenVertically

      if v['name'] == 'is_date':
        return IsDate

      if v['name'] == 'is_dollar_amount':
        return IsDollarAmount

      if v['name'] == 'is_address':
        return IsAddress

      if v['name'] == 'is_person_name':
        return IsPersonName

      if v['name'] == 'is_entire_phrase':
        return IsEntirePhrase

    assert False

  return validate(instantiate(
    BlueprintModel,
    blob,
    base_classes={Entity, Node, Predicate, Rule}, # type: ignore # FIXME
    derived_class_resolver=derived_class_resolver,
    forward_ref_resolver={'Rule': Rule}, # type: ignore
  ))


def load_model(path: Path) -> BlueprintModel:
  with path.open() as f:
    return load_model_from_json(json.load(f))


def save_model(root: BlueprintModel, path: Path) -> None:
  s = json.dumps(asdict(validate(root)), indent=2, sort_keys=True)
  with path.open('w') as f:
    f.write(s + '\n')


if __name__ == '__main__':
  model = load_model(Path(argv[1]))
  if len(argv) > 2:
    save_model(model, Path(argv[2]))
