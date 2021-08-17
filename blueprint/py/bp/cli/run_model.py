"""Run a Blueprint model from the command line."""

import os

from argparse import _SubParsersAction, Namespace
from concurrent.futures import FIRST_EXCEPTION, ProcessPoolExecutor, wait
from dataclasses import asdict, dataclass, replace
from itertools import chain
from multiprocessing import Manager
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from ..bound_tree import BoundNode
from ..bp_logging import bp_logging, configure_cli_logging
from ..config import Config, load_config
from ..document import Document, load_doc
from ..extraction import Extraction, load_extraction
from ..functional import all_equal, nonempty, uniq
from ..google_ocr_file import load_doc_from_google_ocr
from ..ibocr_file import load_doc_from_ibocr
from ..model import load_model, save_model
from ..results import save_results
from ..run import run_model
from ..scoring import ScoredExtraction
from ..synthesis.synthesize import synthesize_pattern_node
from ..targets import TargetsSchema, load_schema
from ..tree import Node


DEFAULT_NUM_SUBPROCESSES = 4
DEFAULT_TIMEOUT = 45


def main_run_model(args: Namespace) -> None:

  # Configure logging
  # =================

  configure_cli_logging(args.verbose)

  # Set config
  # ==========

  config: Config = Config()

  if args.bundle:
    bundle_config_path = Path(args.bundle) / Path('blueprint_config.json')
    if bundle_config_path.is_file():
      config = load_config(bundle_config_path)

  if args.timeout:
    config = replace(config, timeout=args.timeout)

  if args.num_samples is not None \
      and config.num_samples != args.num_samples:
    config = replace(config, num_samples=args.num_samples)

  # Load model
  # ==========

  if args.root:
    root = args.root
  else:
    if args.model:
      model_path = Path(args.model)
    elif args.bundle:
      model_path = Path(args.bundle) / Path('model.json')
      if not model_path.is_file():
        raise RuntimeError('invalid bundle; missing model.json')
    else:
      raise RuntimeError('model required')
    root = load_model(model_path)

  # Figure out the input docs to process
  # ====================================

  def read_paths_from_file(path: Path) -> List[Path]:
    file_paths = list(map(
      Path, filter(lambda s: s, path.read_text().split('\n'))))
    def compute_path(file_path: Path) -> Path:
      if file_path.is_absolute():
        return file_path
      else:
        return path.parent / file_path
    return list(map(compute_path, file_paths))

  docs: Tuple[Document, ...] = tuple()
  if args.bundle:
    doc_path = Path(args.bundle) / Path('selectedDoc.json')
    if not doc_path.is_file():
      raise RuntimeError('invalid bundle; missing selectedDoc.json')
    docs += (load_doc(doc_path),)
  if args.doc_jsons:
    doc_paths = [Path(p) for p in args.doc_jsons]
    docs += tuple(load_doc(path) for path in doc_paths)
  if args.doc_jsons_list:
    doc_paths = read_paths_from_file(Path(args.doc_jsons_list))
    docs += tuple(load_doc(path) for path in doc_paths)

  if args.google_ocr_jsons:
    docs += tuple(load_doc_from_google_ocr(Path(path))
      for path in args.google_ocr_jsons)
  if args.ibocr_jsons:
    docs += tuple(load_doc_from_ibocr(Path(path))
      for path in args.ibocr_jsons)

  # Set up the output directory
  # ===========================

  output_dir = Path(args.output_dir) if args.output_dir else None
  if output_dir:
    output_dir.mkdir(parents=True, exist_ok=True)

  # Run
  # ===

  bp_logging.info('Processing documents')

  for doc in docs:

    # Process this doc
    # ================

    # Run extraction
    # --------------

    bp_logging.info(f'Processing {doc.name}')
    results = run_model(doc, root, config)

    # Write output for this doc
    # -------------------------

    if output_dir:
      bp_logging.info(f'Writing output for {doc.name}')

      # FIXME: doc.name doesn't really mean 'name' anymore.
      doc_name = doc.name.split('/')[-1]
      result_path = output_dir / Path(doc_name)
      if not str(result_path).lower().endswith('.json'):
        result_path = Path(str(result_path) + '.json')
      bp_logging.debug(f'Output file path: {result_path}')

      save_results(results, result_path)


def init_run_model(subparsers: _SubParsersAction) -> None:
  parser = subparsers.add_parser('run_model')
  parser.add_argument('-m', '--model',
    help='BLUEPRINT MODEL',
    type=str, metavar='FILE')
  parser.add_argument('-d', '--doc-jsons',
    help='Document JSON files for input documents',
    type=str, metavar='FILE', nargs='*', default=list())
  parser.add_argument('-D', '--doc-jsons-list',
    help='File with a list of Document JSON paths; '
    'paths may be absolute, '
    'or relative to the directory containing this file',
    type=str, metavar='LIST_FILE')
  parser.add_argument('-g', '--google-ocr-jsons',
    help='Google OCR JSON files for input documents',
    type=str, metavar='FILE', nargs='*', default=list())
  parser.add_argument('-i', '--ibocr-jsons',
    help='IBOCR JSON files for input documents',
    type=str, metavar='FILE', nargs='*', default=list())

  parser.add_argument('-o', '--output-dir',
    help='Output directory',
    type=str)

  parser.add_argument('-b', '--bundle',
    help='Directory containing model and Document JSON files',
    type=str)

  parser.add_argument('-v', '--verbose',
    help='Turn on verbose DEBUG logging to STDOUT',
    action='count', default=0)

  parser.add_argument('-n', '--num-samples',
    help='Examine this many samples from the extraction tree',
    type=int)

  parser.add_argument('-N', '--num-subprocesses',
    help='The number of subprocesses to fork '
    f'(default={DEFAULT_NUM_SUBPROCESSES})',
    type=int, default=DEFAULT_NUM_SUBPROCESSES)
  parser.add_argument('-t', '--timeout',
    help='The timeout, in seconds, per document '
    f'(default={DEFAULT_TIMEOUT})',
    type=int, default=DEFAULT_TIMEOUT)

  parser.set_defaults(func=main_run_model)
