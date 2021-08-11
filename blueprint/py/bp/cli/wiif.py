"""Run WIIF from the command line."""

from argparse import _SubParsersAction, Namespace
from pathlib import Path

from ..document import load_doc
from ..extraction import load_extraction
from ..model import load_model
from ..synthesis.wiif import save_wiif_node, why_is_it_failing


def main_wiif(args: Namespace) -> None:

  document = load_doc(Path(args.doc_json))
  extraction = load_extraction(Path(args.extraction_json))
  node = load_model(Path(args.node_json))

  wiif_node = why_is_it_failing(extraction, node, document)
  save_wiif_node(wiif_node, Path(args.output_file))


def init_wiif(subparsers: _SubParsersAction) -> None:
  parser = subparsers.add_parser('wiif')

  parser.add_argument('-d', '--doc-json',
    help='Document JSON file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-e', '--extraction-json',
    help='Extraction file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-n', '--node-json',
    help='Node file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-o', '--output-file',
    help='Output file',
    type=str, metavar='FILE', required=True)

  parser.set_defaults(func=main_wiif)
