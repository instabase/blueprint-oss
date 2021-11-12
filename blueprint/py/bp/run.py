"""Execute a Blueprint model against an input document."""

import json
import logging

from typing import Dict, Optional

from .bound_tree import BoundNode
from .bp_logging import bp_logging
from .config import Config
from .document import Document
from .entity import Entity, dump_to_json
from .results import Results, generate_results
from .runtime_tracker import DocRuntimeInfo, RuntimeTracker, Step
from .timeout import timeout
from .tree import Node, optimize_rule_distribution


def run_model(doc: Document, root: Node, config: Config=Config()) \
    -> Results:
  """Run the given Blueprint model on a Document.

  Args:
    doc: A Blueprint Document.
    root: The root of an extraction tree.
    config: Run configuration.
  """

  def run_with_runtime_tracker(runtime_tracker: RuntimeTracker) -> BoundNode:

    if config.num_samples == 0:
      bp_logging.warning(
        'Requested 0 extraction samples; '
        'no extractions will be generated')

    if not runtime_tracker:
      # We don't use this. We initialize it to avoid a ton of if statements
      # in the code below.
      runtime_tracker = RuntimeTracker()
    assert isinstance(runtime_tracker, RuntimeTracker)

    bp_logging.info('Binding extraction tree')
    runtime_tracker.start(Step.BINDING)
    optimized_root = optimize_rule_distribution(root)
    optimized_root.validate()
    bound_root = optimized_root.bound_to(doc)
    runtime_tracker.end(Step.BINDING)

    try:
      bp_logging.info('Pumping extraction tree')
      runtime_tracker.start(Step.PUMPING)
      def done() -> bool:
        if config.num_samples < 0:
          return False
        else:
          return bound_root.num_extractions_generated == config.num_samples
      while not done():
        next(bound_root)
    except StopIteration:
      if config.num_samples > 0:
        bp_logging.warning(
          f'Ran out of samples before {config.num_samples} were found')
    finally:
      runtime_tracker.end(Step.PUMPING)
    assert bound_root.best_extraction is not None
    best_extraction = {point.field: point.entity.entity_text
      for point in bound_root.best_extraction.extraction.assignments}
    bp_logging.debug(f'Best extraction for {doc.name}: '
      f'{json.dumps(best_extraction, indent=2, sort_keys=True)}')

    return bound_root


  runtime_tracker = RuntimeTracker()
  runtime_tracker.start(Step.TOTAL)

  timed_out = False
  bound_node: Optional[BoundNode] = None
  try:
    if config.timeout != -1:
      bound_node = timeout(config.timeout,
        lambda: run_with_runtime_tracker(runtime_tracker))
    else:
      bound_node = run_with_runtime_tracker(runtime_tracker)
  except TimeoutError:
    bp_logging.info(f'Extraction timed out for {doc.name}. ')
    timed_out = True

  runtime_tracker.end(Step.TOTAL)
  runtime_tracker.finish() # Janky.

  bp_logging.debug(f'Total time: {runtime_tracker.duration_ms(Step.TOTAL)}')

  runtime_info = DocRuntimeInfo(
    binding_ms=runtime_tracker.duration_ms(Step.BINDING),
    pumping_ms=runtime_tracker.duration_ms(Step.PUMPING),
    total_ms=runtime_tracker.duration_ms(Step.TOTAL),
    timed_out=timed_out)

  return generate_results(bound_node, runtime_info)
