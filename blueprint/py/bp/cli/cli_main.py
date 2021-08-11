#!/usr/bin/env python3

"""The Blueprint CLI."""

import os

from argparse import ArgumentParser, Namespace
from sys import stderr
from typing import Optional

from ..bp_logging import configure_cli_logging
from .run_model import init_run_model
from .synthesis import init_synthesis
from .wiif import init_wiif
from ..config import Config
from ..tree import Node


def bp_cli_main(root: Optional[Node] = None,
                config: Optional[Config] = None) -> None:

  configure_cli_logging(1)

  parser = ArgumentParser(prog='Blueprint')
  parser.set_defaults(root_parser=parser)

  subparsers = parser.add_subparsers()

  init_run_model(subparsers)
  init_synthesis(subparsers)
  init_wiif(subparsers)

  args = parser.parse_args()

  if getattr(args, 'func', None) is None:
    parser.print_help(stderr)
    exit(-1)

  args.root = root if root is not None else None
  if config is not None:
    args.config = config

  args.func(args)


if __name__ == '__main__':
  bp_cli_main()
