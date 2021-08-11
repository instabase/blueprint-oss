from typing import Dict, Tuple

from ..string_algos import relative_edit_distance


def date_likeness(text: str) -> Tuple[float, Dict]:
  # FIXME: This is all very janky.

  if len(text) > 20:
    return (0, {'text_too_long': True})

  text = text.upper()

  long_months = {
      'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST',
      'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
  }
  short_months = {
      'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT',
      'NOV', 'DEC'
  }

  for long_month in long_months:
    text = text.replace(long_month, 'JAN')
  for short_month in short_months:
    text = text.replace(short_month, 'JAN')

  for digit in '012345678':
    text = text.replace(digit, '9')

  text = text.replace('/', '-')
  text = text.replace('9.9', '9-9')
  text = text.replace('.', ' ')
  text = text.replace(',', ' ')
  text = '99'.join(text.rsplit('9999', 1))
  text = '-'.join(text.split())

  patterns = [
      'JAN-99-99',
      'JAN-99TH-99',
      '99-JAN-99',
      '99TH-JAN-99',
      '99-99-99',
      '99JAN99',
  ]

  scores = {
      pattern: 1 - relative_edit_distance(pattern, text) for pattern in patterns
  }
  return (max(scores.values()), scores)


def dollar_amount_likeness(text: str) -> float:
  if text == '.00':
    return 1  # FIXME: This method needs to be revisited.

  if len(text) > 15:
    return 0

  digits = '0123456789'
  seps = ',. '
  symbols = '$'
  other_legal = '*'

  legal_chars = digits + seps + symbols + other_legal

  num_digits = len([c for c in text if c in digits])
  num_seps = len([c for c in text if c in seps])
  num_symbols = len([c for c in text if c in symbols])
  num_other_legal = len([c for c in text if c in other_legal])

  num_legal_chars = num_digits + num_seps + num_symbols + num_other_legal

  # FIXME: Magic numbers.
  if num_digits > 14 or len(text) < 3:
    return 0

  prefix_trash = 0
  for c in text:
    if c in legal_chars:
      break
    prefix_trash += 1
  suffix_trash = 0
  for c in reversed(text):
    if c in legal_chars:
      break
    suffix_trash += 1

  text = text[prefix_trash:len(text) - suffix_trash]

  cents_trash = 0
  if len(text) > 0 and text[-1] not in digits:
    cents_trash += 1
  if len(text) > 1 and text[-2] not in digits:
    cents_trash += 1
  if len(text) > 2 and text[-3] not in seps:
    cents_trash += 1

  min_num_digits = 3

  max_num_seps = int(0.25 * (num_legal_chars - num_symbols))
  max_num_symbols = 1

  error = len(text) - num_legal_chars
  error += max(0, min_num_digits - num_digits)
  error += max(0, num_seps - max_num_seps)
  error += max(0, num_symbols - max_num_symbols)
  error += prefix_trash
  error += suffix_trash
  error += cents_trash

  def taper_error(raw_error: float, tolerance: float, taper: float) -> float:
    assert raw_error >= 0.0
    assert tolerance >= 0.0
    assert taper >= 0.0
    error = max(0.0, raw_error - tolerance)
    if error == 0.0:
      return 1.0
    if taper == 0.0:
      return 0.0
    # abs to avoid -0.0 in output.
    return abs(1.0 - min(1.0, error / taper))

  # FIXME: Magic numbers.
  return taper_error(error, 0, 0.5 * len(text))
