import logging

from typing import Any, Optional


class _BlueprintLogging:
  def __init__(self) -> None:
    self.logger = logging.getLogger('blueprint')
    self.logger.setLevel(logging.DEBUG)

    self.debug = self.logger.debug
    self.info = self.logger.info
    self.warning = self.logger.warning
    self.error = self.logger.error

    self.initialized = False


bp_logging = _BlueprintLogging()


def configure_cli_logging(verbosity: int) -> None:
  """Turn on logging to STDOUT.

  This refers to usual runtime logs, not extraction results/output.

  Args:
    verbosity: Set to 0 for INFO logging, 1 or higher for DEBUG logging.
  """

  if not bp_logging.initialized:
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    if verbosity >= 0:
      console_handler = logging.StreamHandler()
      console_handler.setLevel(logging.INFO if verbosity == 0 else logging.DEBUG)
      console_handler.setFormatter(formatter)
      bp_logging.logger.addHandler(console_handler)

    bp_logging.debug('Configured logging')
    bp_logging.initialized = True
