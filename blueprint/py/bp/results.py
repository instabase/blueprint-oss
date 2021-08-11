"""A Blueprint extraction results file format.

This stores the results of running a BP extraction model from Studio on a single
document.
"""

import json

from dataclasses import asdict, dataclass, replace
from functools import reduce
from itertools import chain
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .bound_tree import BoundNode, BoundPatternNode
from .entity import Entity
from .geometry import BBox, Interval
from .instantiate import instantiate
from .rule import RuleScore as BPRuleScore, Rule
from .runtime_tracker import DocRuntimeInfo, RuntimeTracker, Step
from .scoring import ScoredExtraction
from .targets import DocTargets, TargetValue


@dataclass(frozen=True)
class ResultsNode:
  node_uuid: str
  top_20_extractions: Tuple[ScoredExtraction, ...]
  top_score: float
  child_nodes: Tuple['ResultsNode', ...]
  fields: Tuple[str, ...]


def validate_results_node(results_node: ResultsNode) -> ResultsNode:
  assert results_node.top_20_extractions
  if results_node.top_20_extractions[0].score != results_node.top_score:
    raise ValueError(f'results node {results_node.node_uuid} top score '
                    f'{results_node.top_score} does not match the score in top '
                    'extraction')
  for child in results_node.child_nodes:
    validate_results_node(child)
  return results_node


@dataclass(frozen=True)
class Results:
  root: Optional[ResultsNode]
  runtime_info: DocRuntimeInfo


def validate(results: Results) -> Results:
  if results.root is not None:
    validate_results_node(results.root)
  return results


def generate_results(root: Optional[BoundNode], runtime_info: DocRuntimeInfo) \
    -> Results:
  def generate_results_tree(bound_node: BoundNode) -> ResultsNode:
    assert bound_node.best_extraction is not None
    return ResultsNode(
      node_uuid=bound_node.uuid,
      top_20_extractions=tuple(sorted(bound_node.returned_extractions)),
      top_score=bound_node.best_extraction.score,
      fields=tuple(bound_node.legal_fields),
      child_nodes=tuple(generate_results_tree(child)
        for child in bound_node.child_nodes
        if not isinstance(bound_node, BoundPatternNode)))

  results_tree = generate_results_tree(root) if root is not None else None
  return validate(Results(results_tree, runtime_info))


def load_results(path: Path) -> Results:
  with path.open() as f:
    return validate(instantiate(Results, json.load(f)))


def save_results(result: Results, path: Path) -> None:
  with path.open('w') as f:
    json.dump(asdict(validate(result)), f, indent=2, sort_keys=True)
