"""Utilities for unit/integration testing Blueprint code."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, Iterable

from .mock_doc import MockWord

from bp.config import Config
from bp.document import Document
from bp.extraction import Field, Extraction
from bp.run import run_model
from bp.scoring import ScoredExtraction
from bp.timeout import timeout
from bp.tree import Node


@dataclass(frozen=True)
class ExpectedExtraction:
  """A description of an extraction we expect to come out when we run a
  particular Blueprint model against some input document.

  Args:
    doc: A Document, typically a mock document.
    dictionary: A dictionary from field to text. To make it easier to describe
      expected extractions, we don't require test authors to give a full
      field-to-entity dictionary.
  """

  doc: Document
  dictionary: Dict[Field, str]

  @property
  def fields(self) -> FrozenSet[Field]:
    return frozenset(self.dictionary.keys())

  def is_exactly_best_extraction_from(self, node: Node) -> bool:
    """Is the expected extraction equal to the top-scoring extraction from this
    tree?"""
    return self.matches_best_extraction_from(node, exact=True)

  def is_contained_in_best_extraction_from(self, node: Node) -> bool:
    """Is the expected extraction contained in the top-scoring extraction from
    this tree?"""
    return self.matches_best_extraction_from(node, exact=False)

  def matches_best_extraction_from(self, node: Node, exact: bool) -> bool:
    """Does the expected extraction match the top-scoring extraction from this
    extraction tree?

    Args:
      node: An extraction tree.
      exact: Whether an exact match is desired. If not, then it is allowed for
        the top-scoring extraction from the tree to have extra fields set (for
        example, anchors) which are not present in this expected extraction.
    """
    results = run_model(self.doc, node)
    if results.root is None:
      # Extraction timed out.
      return False
    assert len(results.root.top_20_extractions) > 0
    best_extraction = results.root.top_20_extractions[0]
    return self.matches(best_extraction.extraction, exact)

  def matches(self, extraction: Extraction, exact: bool) -> bool:
    """Does the given extraction match this expected extraction?

    Args:
      extraction: An extraction to compare to.
      exact: Whether an exact match is desired. If not, then it is allowed for
        extraction to have extra fields set (for example, anchors) which are not
        present in this expected extraction.
    """
    if exact and extraction.fields != self.fields:
      return False
    if not self.fields <= extraction.fields:
      return False
    return all(extraction[field].entity_text == self.dictionary[field]
      for field in self.dictionary)


def no_nontrivial_extractions(doc: Document, node: Node) -> bool:
  """Does this node have no non-trivial extractions from this document?

  In other words, does this extraction tree fail to match this document at all?
  """

  results = run_model(doc, node, Config(num_samples=-1))
  if results.root is None:
    # Extraction timed out.
    return False
  assert len(results.root.top_20_extractions) > 0
  best_extraction = results.root.top_20_extractions[0]
  assert best_extraction is not None
  return best_extraction.is_empty


def raises_exception(doc: Document, exception: Any, node: Node) -> bool:
  """Does this node raise the given exception when run for this document?"""

  try:
    bound_node = run_model(doc, node)
  except exception:
    return True
  return False


def times_out(timeout_time: int, f: Callable[[], Any]) -> bool:
  """Says that a function takes at least this long to run.

  Args:
    f: A function taking no arguments. The return value is discarded.
    timeout_time: The minimum amount of time that f() should take to run, in seconds.
  """

  try:
    timeout(timeout_time, f)
    return False
  except TimeoutError:
    return True
