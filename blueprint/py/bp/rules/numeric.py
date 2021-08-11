"""Blueprint rules related to entities having numeric type."""

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple
from uuid import uuid4

from .logical import any_holds
from ..document import Document, Entity
from ..rule import AtomScore, Degree1Predicate, DegreeError, Predicate, RuleScore


def _sum(
    Es: Tuple[Entity, ...], coefficients: Tuple[float, ...],
    period_as_delimiter: bool, force_dollar_decimal: bool) -> Optional[float]:

  def numeric(s: Optional[str]) -> str:
    result = ''
    if s is None:
      return result
    drop_remaining_periods = not period_as_delimiter
    for i in range(len(s) - 1, -1, -1):
      if s[i] in '0123456789':
        result += s[i]
      if s[i] == '-':
        if i == 0:
          result += s[i]
        else:
          # There is a random minus sign in the middle of the "number"...
          pass
      if not drop_remaining_periods and s[i] == '.':
        result += s[i]
        drop_remaining_periods = True

    if len(result) == 1 and result == '.':
      result = ''

    result = ''.join(reversed(result))

    if force_dollar_decimal:
      if '.' not in result and len(result) > 2:
        result = result[:-2] + '.' + result[-2:]

    return result

  if len(Es) != len(coefficients):
    raise DegreeError(
        'zero_sum entity list has to be equal in length to coefficients list')

  # FIXME: We should use ints when both strings are ints. (For precision.)

  ss = tuple(numeric(E.entity_text) for E in Es)

  if not all(ss):
    return None

  try:
    fs = tuple(map(float, ss))
  except ValueError:
    return None

  return sum(f * c for f, c in zip(fs, coefficients))


@dataclass(frozen=True)
class SumIsApproximately(Predicate):
  amount: float
  coefficients: Tuple[float, ...]
  tolerance: float
  taper: float
  period_as_delimiter: bool
  force_dollar_decimal: bool

  def __init__(
    self,
    amount: float,
    coefficients: Tuple[float, ...],
    tolerance: float,
    taper: float,
    period_as_delimiter: bool,
    force_dollar_decimal: bool,
    name: str = 'sum_is_approximately',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'amount', amount)
    object.__setattr__(self, 'coefficients', coefficients)
    object.__setattr__(self, 'tolerance', tolerance)
    object.__setattr__(self, 'taper', taper)
    object.__setattr__(self, 'period_as_delimiter', period_as_delimiter)
    object.__setattr__(self, 'force_dollar_decimal', force_dollar_decimal)

  @property
  def degree(self) -> int:
    return len(self.coefficients)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    s = _sum(
      entities,
      self.coefficients,
      self.period_as_delimiter,
      self.force_dollar_decimal)
    if s is None:
      return AtomScore(0)
    error = max(0, abs(s - self.amount) - self.tolerance)
    if self.taper == 0:
      return AtomScore(1) if error == 0 else AtomScore(0)
    assert error >= 0 and self.taper > 0
    return AtomScore(1 - min(1, error / self.taper))


def sum_is_approximately(
    amount: float,
    coefficients: Iterable[float],
    tolerance: float = 0.5,
    taper: float = 0.5,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that some fields are numbers, and that if we take their sum with the
  given coefficients, then we get something close to the given amount.

  Args:
    amount: The approximate target value of the sum.
    coefficients: See example.
    tolerance: How far from the target amount the sum is allowed to be without
      penalty.
    taper: The score of this rule tapers down from 1 to 0 over this distance as
      abs(sum - amount) grows from tolerance to tolerance+taper.
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    # Says that 2 * guests + 1 * hosts ~= 10, plus or minus 5
    sum_is_approximately(10, [2, 1], tolerance=5)('guests', 'hosts')
  """

  if tolerance < 0:
    raise ValueError(f'tolerance must be nonnegative, not {tolerance}')
  if taper < 0:
    raise ValueError(f'taper must be nonnegative, not {taper}')

  coefficients = tuple(coefficients)
  assert isinstance(coefficients, tuple)

  return SumIsApproximately(
      name=f'sum_is_approximately('
      f'amount={amount}, '
      f'coefficients={coefficients}, '
      f'tolerance={tolerance}, '
      f'taper={taper}, '
      f'period_as_delimiter={period_as_delimiter}, '
      f'force_dollar_decimal={force_dollar_decimal})',
      amount=amount,
      coefficients=tuple(coefficients),
      tolerance=tolerance,
      taper=taper,
      period_as_delimiter=period_as_delimiter,
      force_dollar_decimal=force_dollar_decimal)


def sum_is_near_zero(
    coefficients: Iterable[float],
    tolerance: float = 0.5,
    taper: float = 0.5,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that some fields are numbers, and that if we take their sum with the
  given coefficients, then we get something close to zero.

  Args:
    coefficients: See example.
    tolerance: How far from zero the sum is allowed to be without penalty. This
      is used in a weak inequality: in other words, we allow
      abs(sum) == tolerance.
    taper: The score of this rule tapers down from 1 to 0 over this distance as
      abs(sum) grows from tolerance to tolerance+taper.
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    # Says that abs(gross_pay - deductions - net_pay) <= 0.5
    sum_is_near_zero([1, -1, -1], tolerance=0.5) \
      ('gross_pay', 'deductions', 'net_pay')
  """

  coefficients = tuple(coefficients)
  assert isinstance(coefficients, tuple)

  return sum_is_approximately(
    0, coefficients, tolerance, taper,
    period_as_delimiter, force_dollar_decimal)


def sum_is_zero(
    coefficients: Iterable[float],
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that some fields are numbers, and that if we take their sum with the
  given coefficients, then we get zero.

  Args:
    coefficients: See example.
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    # Says that gross_pay - deductions - net_pay = 0
    sum_is_zero([1, -1, -1])('gross_pay', 'deductions', 'net_pay')
  """

  coefficients = tuple(coefficients)
  assert isinstance(coefficients, tuple)

  return sum_is_near_zero(
    coefficients,
    tolerance=0,
    taper=0,
    period_as_delimiter=period_as_delimiter,
    force_dollar_decimal=force_dollar_decimal)


@dataclass(frozen=True)
class SumIsAtLeast(Predicate):
  lower_bound: float
  coefficients: Tuple[float, ...]
  strict: bool
  period_as_delimiter: bool
  force_dollar_decimal: bool

  def __init__(
    self,
    lower_bound: float,
    coefficients: Tuple[float, ...],
    strict: bool,
    period_as_delimiter: bool,
    force_dollar_decimal: bool,
    name: str = 'sum_is_at_least',
    uuid: Optional[str] = None,
  ):
    super().__init__(
      name = name,
      uuid = str(uuid4()) if uuid is None else uuid,
    )
    object.__setattr__(self, 'lower_bound', lower_bound)
    object.__setattr__(self, 'coefficients', coefficients)
    object.__setattr__(self, 'strict', strict)
    object.__setattr__(self, 'period_as_delimiter', period_as_delimiter)
    object.__setattr__(self, 'force_dollar_decimal', force_dollar_decimal)

  @property
  def degree(self) -> int:
    return len(self.coefficients)

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> RuleScore:
    s = _sum(
      entities,
      self.coefficients,
      self.period_as_delimiter,
      self.force_dollar_decimal)
    if s is None:
      return AtomScore(0)
    if s > self.lower_bound or (not self.strict and s == self.lower_bound):
      return AtomScore(1)
    return AtomScore(0)


def sum_is_at_least(
    lower_bound: float,
    coefficients: Iterable[float],
    strict: bool = True,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that some fields are numbers, and that if we take their sum with the
  given coefficients, then we get a number greater than (or equal to) the given
  bound.

  Args:
    lower_bound: The minimum value of the sum.
    coefficients: See example.
    strict: Whether to use a strict inequality (>) rather than a weak one (>=).
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    # Says that 1 * normal_pay + 2 * overtime_pay >= 500
    sum_is_at_least(500, [1, 2])('normal_pay', 'overtime_pay')
  """

  coefficients = tuple(coefficients)
  assert isinstance(coefficients, tuple)

  return SumIsAtLeast(
    name=f'sum_is_at_least('
    f'lower_bound={lower_bound}, '
    f'coefficients={coefficients}, '
    f'strict={strict}, '
    f'period_as_delimiter={period_as_delimiter}, '
    f'force_dollar_decimal={force_dollar_decimal})',
    lower_bound=lower_bound,
    coefficients=coefficients,
    strict=strict,
    period_as_delimiter=period_as_delimiter,
    force_dollar_decimal=force_dollar_decimal)


def sum_is_positive(
    coefficients: Iterable[float],
    strict: bool = True,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that some fields are numbers, and that if we take their sum with the
  given coefficients, then we get a number greater than (or equal to) zero.

  Args:
    coefficients: See example.
    strict: Whether to use a strict inequality (>) rather than a weak one (>=).
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example:
    # Says that net_pay >= 0.5 * gross_pay
    sum_is_positive([1, -0.5])('net_pay', 'gross_pay')
  """

  coefficients = tuple(coefficients)
  assert isinstance(coefficients, tuple)

  return sum_is_at_least(
    0, coefficients, strict,
    period_as_delimiter, force_dollar_decimal)


def is_nearly_equal_to(
    amount: float,
    tolerance: float = 0.5,
    taper: float = 0.5,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that a field is equal to the given amount, within a certain tolerance.

  Args:
    amount: The constant to compare against.
    tolerance: How far from the target amount the sum is allowed to be without
      penalty.
    taper: The score of this rule tapers down from 1 to 0 over this distance as
      abs(sum - amount) grows from tolerance to tolerance+taper.
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    # Says that days_in_month is equal to 29.5 +/- 1.5 (aka between 28 and 31)
    is_nearly_equal_to(29.5, tolerance=1.5)('days_in_month')
  """
  return sum_is_approximately(
      amount, [1], tolerance, taper, period_as_delimiter,
      force_dollar_decimal)


def is_equal_to(amount: float) -> Predicate:
  """Says that a field is exactly equal to some constant amount."""
  return is_nearly_equal_to(amount, tolerance=0, taper=0)


def is_greater_than(
    amount: float,
    strict: bool = True,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that a field is greater than some constant amount.

  Args:
    amount: The constant to compare against.
    strict: Whether to use a strict inequality (>) rather than a weak one (>=).
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    is_greater_than(0)('net_pay')
  """
  return sum_is_at_least(
    amount, [1], strict,
    period_as_delimiter, force_dollar_decimal)


def is_less_than(
    amount: float,
    strict: bool = True,
    period_as_delimiter: bool = False,
    force_dollar_decimal: bool = False) -> Predicate:
  """Says that a field is less than some constant amount.

  Args:
    amount: The constant to compare against.
    strict: Whether to use a strict inequality (<) rather than a weak one (<=).
    period_as_delimiter: This argument controls whether the right-most period in
      OCRed text gets treated as a decimal delimiter, or gets stripped. We strip
      all non-numeric characters by default. Periods are often lost during OCR,
      so for example if you are dealing with dollar values, it's better to
      assume that the last two digits are cents regardless of whether a period
      is present, and discard all punctuation. Hence the default value of False.
    force_dollar_decimal: If this is true, then when converting OCRed text to
      numeric values, we insert a decimal point at the third-to-last character
      if one is not already present -- in other words, this enforces that the
      text is in the format dollars.cents, where cents is two digits long.

  Example code:
    is_less_than(40, strict=False)('hours_worked')
  """
  return sum_is_at_least(
    -amount, [-1], strict, period_as_delimiter,
    force_dollar_decimal)


"""Says that two fields are equal as numeric values."""
are_equal = sum_is_zero([1, -1])


"""
  Says that the first of two fields is greater than the second.

  Example code:
    greater_than('gross_pay', 'tax_deductions')
"""
greater_than = sum_is_positive([1, -1])


"""
  Says that the first of two fields is greater than or equal to the second.

  Example code:
    greater_than_or_equal_to('total_hours_worked', 'overtime_hours_worked')
"""
greater_than_or_equal_to = sum_is_positive([1, -1], strict=False)


"""
  Says that the first of two fields is less than the second.
"""
less_than = sum_is_positive([-1, 1])


"""
  Says that the first of two fields is less than or equal to the second.
"""
less_than_or_equal_to = sum_is_positive([-1, 1], strict=False)


"""
  Says that a field is a numeric value equal to zero.

  Example code:
    extract(
      text_equals('Balance:')('balance_label'),
      is_dollar_amount('balance'),
      row('balance_label', 'balance'),
      is_zero('balance'))
"""
is_zero = is_equal_to(0)


"""Says that a field is a positive numeric value."""
is_positive = is_greater_than(0)


"""Says that a field is a negative numeric value."""
is_negative = is_less_than(0)


"""Says that a field is a nonnegative numeric value."""
is_nonnegative = is_greater_than(0, strict=False)
