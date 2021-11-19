"""An implementation for function timeouts that uses signal.SIGALRM."""

from signal import SIG_DFL, SIGALRM, alarm, getsignal, signal
from typing import Any, Callable

from .bp_logging import bp_logging


def timeout(timeout: int, f: Callable[[], Any]) -> Any:
  """Calls a function and sets a timeout.

  Args:
    timeout: The maximum amount of time that f() should take to run, in seconds.
    f: A function taking no arguments. If f finishes running before the
      timeout we return f's result.
  """

  def handle_timeout(signum: int, _: Any) -> None:
    bp_logging.info('Handling timeout')
    raise TimeoutError

  # handler = getsignal(SIGALRM)
  # if handler != SIG_DFL:
  #   raise RuntimeError('attempted to use SIGALRM to wrap a function timeout, '
  #     f'but {handler} is already registered as a SIGALRM handler')

  try:
    # signal(SIGALRM, handle_timeout)
    # alarm(timeout)
    return f()
  finally:
    signal(SIGALRM, SIG_DFL)
    alarm(0)
