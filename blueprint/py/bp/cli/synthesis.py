"""Run synthesis from the command line."""

from argparse import _SubParsersAction, Namespace
from pathlib import Path

from ..document import load_doc
from ..extraction import load_extraction
from ..targets import load_schema

from ..bp_logging import bp_logging
from ..model import save_model
from ..synthesis.synthesize import synthesize_pattern_node


def main_synthesis(args: Namespace) -> None:

  bp_logging.info(f'Running synthesis for {args.doc_json}')
  
  doc = load_doc(Path(args.doc_json))
  extraction = load_extraction(Path(args.extraction_json))
  schema = load_schema(Path(args.schema_json))

  results = synthesize_pattern_node(extraction, schema, doc)
  save_model(results, Path(args.output_file))


def init_synthesis(subparsers: _SubParsersAction) -> None:
  parser = subparsers.add_parser('synthesis')

  parser.add_argument('-d', '--doc-json',
    help='Document JSON file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-e', '--extraction-json',
    help='Target extraction file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-s', '--schema-json',
    help='Targets schema file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-o', '--output-file',
    help='Output file',
    type=str,  metavar='FILE', required=True)

  parser.set_defaults(func=main_synthesis)
