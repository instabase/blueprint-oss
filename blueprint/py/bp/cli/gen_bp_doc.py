"""Generate a Blueprint doc from some other format."""

from argparse import _SubParsersAction, Namespace
from pathlib import Path

from ..bp_logging import configure_cli_logging
from ..document import Document, save_doc
from ..google_ocr_file import load_doc_from_google_ocr


def main_gen_bp_doc(args: Namespace) -> None:
  configure_cli_logging(args.verbose)
  doc = load_doc_from_google_ocr(Path(args.google_ocr_json))
  save_doc(doc, Path(args.output_path))


def init_gen_bp_doc(subparsers: _SubParsersAction) -> None:
  parser = subparsers.add_parser('gen_bp_doc')
  parser.add_argument('-g', '--google-ocr-json',
    help='Input Google OCR JSON file',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-o', '--output-path',
    help='Output file name',
    type=str, metavar='FILE', required=True)
  parser.add_argument('-v', '--verbose',
    help='Turn on verbose DEBUG logging to STDOUT',
    action='count', default=0)
  parser.set_defaults(func=main_gen_bp_doc)
