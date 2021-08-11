from typing import NoReturn, Optional, TypeVar


T = TypeVar('T')


def assert_exhaustive(x: NoReturn) -> NoReturn:
  """Takes advantage of mypy's type narrowing to statically check exhaustivity.

  Use this to ensure all type variants of a Union/Enum/etc are cased.

  See: https://github.com/python/mypy/issues/5818

  Example:
    MyUnion = Union[int, str, bytes]

    def my_function(x: MyUnion) -> None:
      if isinstance(x, int):
        ...
      elif isinstance(x, str):
        ...
      # oh no, we forgot to put in a case for bytes!
      else:
        assert_exhaustive(x)  # mypy will catch this statically
  """
  raise AssertionError(f'Unhandled type: {type(x).__name__}')


def unwrap(x: Optional[T]) -> T:
  """ Non-defensively use the value inside an Optional.

  Raises:
    RuntimeError: If x is None
  """
  if x is None:
    raise RuntimeError('Called unwrap() on a None value')
  return x
