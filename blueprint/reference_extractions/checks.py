#!/usr/bin/env python3

from dataclasses import dataclass
from functools import reduce
from itertools import chain
from typing import Callable, Collection, List, Optional, Tuple
from uuid import uuid4

from bp import *
from bp.document import DocRegion, Entity, get_pages
from bp.functional import pairs
from bp.geometry import BBox, Interval
from bp.rule import AtomScore, Degree1Predicate, Degree2Predicate, DegreeError
from bp.string_algos import edit_distance as sa_edit_distance


# Rules
# =====

def _space_above(doc: Document, E: Entity) -> Optional[DocRegion]:
  return DocRegion.build(doc, BBox.build(
      E.bbox.ix, Interval(
          E.bbox.iy.a - doc.median_line_height(),
          E.bbox.iy.a,)))


@dataclass(frozen=True)
class EmptyLineAbove(BoxUnimpinged):

  def __init__(
    self,
    name: str = 'empty_line_above',
  ):
    super().__init__(
      name = name,
      degree_ = 1,
      direction = Orientation.VERTICAL,
    )

  def doc_region_getter(self, doc: Document, *Es: Entity) \
      -> Optional[DocRegion]:
    assert len(Es) == 1
    return _space_above(doc, *Es)


empty_line_above = EmptyLineAbove()


@dataclass(frozen=True)
class IsOrientedHorizontally(Degree1Predicate):

  uuid: str = str(uuid4())
  
  def score(self, entities: Tuple[Entity, ...], doc: Document) -> AtomScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    # FIXME: Actually put a range for this, not just binary.
    # FIXME: This isn't a great judge of orientation.
    if E.bbox.iy.length > E.bbox.ix.length * 1.5:
        return AtomScore(0)
    return AtomScore(1)


def is_oriented_horizontally() -> Degree1Predicate:
  return IsOrientedHorizontally(name='is_oriented_horizontally')


@dataclass(frozen=True)
class IsInPixelPageRegion(Degree1Predicate):
  y_offset_pixels: float
  direction: Direction

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> AtomScore:
    if len(entities) != 1:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E = entities[0]
    page_height = sum(page.bbox.height for page in get_pages(E, doc))
    if self.y_offset_pixels >= page_height:
      return AtomScore(1)

    # FIXME: This ignores the rotation/orientation of the documents.
    # FIXME: This does not differentiate among the pages.

    if self.direction == Direction.TOP_DOWN:
      y_range_px = Interval(0.0, self.y_offset_pixels)
    else:
      if self.direction != Direction.BOTTOM_UP:
        raise ValueError('Invalid direction')
      y_range_px = Interval(page_height - self.y_offset_pixels, page_height)

    y_percentage = y_range_px.contains_percentage_of(E.bbox.iy) \
        if y_range_px else 1

    return AtomScore(y_percentage)


# FIXME: Do this based off of percentage of page width instead of pixels
# FIXME: Add x-direction
def is_in_pixel_page_region(
    y_offset_pixels: float, direction: Direction) -> Degree1Predicate:
  return IsInPixelPageRegion(
      name=f'is_in_pixel_page_region(y_offset_pixels={y_offset_pixels})',
      y_offset_pixels=y_offset_pixels, direction=direction, uuid=str(uuid4()))


@dataclass(frozen=True)
class EntityStringsAreDisjoint(Degree2Predicate):
  # FIXME: Add some taper for this.

  uuid: str = str(uuid4())

  def score(self, entities: Tuple[Entity, ...], doc: Document) -> AtomScore:
    if len(entities) != 2:
      raise DegreeError(f'wrong number of entities passed to {self}.score')
    E1, E2 = entities[0], entities[1]
    if E1.entity_text is None or E2.entity_text is None:
      return AtomScore(1)
    if frozenset(E1.entity_text.split()) & frozenset(E2.entity_text.split()):
      return AtomScore(0)
    return AtomScore(1)


def entity_strings_are_disjoint() -> Degree2Predicate:
  return EntityStringsAreDisjoint(name='entity_strings_are_disjoint()')


def entity_strings_are_pairwise_disjoint(*fields: Field) -> Collection[Rule]:
  return [entity_strings_are_disjoint()(i1, i2) for i1, i2 in pairs(fields)]


def _taper_error(raw_error: int, tolerance: int, taper: int) -> float:
  assert raw_error >= 0
  assert tolerance >= 0
  assert taper >= 0
  error = max(0, raw_error - tolerance)
  if error == 0:
    return 1.0
  if taper == 0:
    return 0.0
  # abs to avoid -0.0 in output.
  return abs(1.0 - min(1.0, error / (taper + 1)))

# Field rules
# ===========

# Labels are left out because they're optional.
check_fields = (
  'check_anchor',
  'date',
  'amount',
  'check_number',
  'payor',
  'pay_to_label',
  'payee',
  'payee_address')

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
NUMBERS = "0123456789"
AMOUNT_SYMBOLS = "$:*,. "
PAYOR_SYMBOLS = "':.,-/ "
DATE_SYMBOLS = ":/-, "
CHECK_NUMBER_SYMBOLS = "- "
MICR_SYMBOLS = ":|"

# FIXME: Add more?
STREET_WORDS = ("STREET","ST","ST.","DRIVE","DR","DR.",
                  "ROAD","RD","RD.","BOX","BLVD","BLVD.")

# FIXME: Only works for US checks
# FIXME: Doesn't work for non-abbreviated states
STATE_ABBREVS = ("AK","AL","AR","AS","AZ","CA","CO","CT","DC","DE","FL","GA",
                "GU","HI","IA","ID","IL","IN","KS","KY","LA","MA","MD","ME",
                "MI","MN","MO","MP","MS","MT","NC","ND", "NE", "NH","NJ", "NM",
                "NV", "NY", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD","TN",
                "TX","UM","UT","VA","VI","VT","WA","WI","WV","WY")

# FIXME: some of these might need to be separated out into specific rules
# eg. one word might be bad for address, but needed for company names / payor
CHECK_WORDS = ('Document','Face','Check','Contains','Order',
                'Pay','To the','Control','Amount')

is_date_label = all_hold(
  any_holds(
      text_equals('Date'),
      text_equals('Date:'),
      text_equals('Check date')))

is_check_date = all_hold(
    is_date,
    text_properties_are(
        length={'at_least': 6},
        legal_chars=LETTERS+NUMBERS+DATE_SYMBOLS,
        tolerance=0, taper=1),
    line_count_is({1:1,2:0}))

# FIXME: Maybe do some sort of substring thing instead of all this.
is_pay_to_label = any_holds(
    text_equals('Pay to'),
    text_equals('To the'),
    text_equals('Order'),
    text_equals('Order of'))

is_check_number_label = all_hold(
    is_entire_phrase,
    any_holds(
        text_equals('No.', tolerance=0),
        text_equals('Check no.'),
        text_equals('Control no.'),
        text_equals('Check'),
        text_equals('Check number'),
        text_equals('Check#')))

is_amount_label = any_holds(
    text_equals('Amount of check'),
    text_equals('Amount'),
    text_equals('Net amount'),
    text_equals('$', tolerance=0, taper=0))

is_amount = all_hold(
    is_dollar_amount,
    text_properties_are(
        length={'at_least': 3},
        legal_chars=NUMBERS+AMOUNT_SYMBOLS,
        min_char_counts=[{'chars': ".", 'count': 1}],
        tolerance=0, taper=2),
    is_entire_phrase)

is_check_anchor = any_holds(
    text_equals('Authorized'),
    text_equals('Signature'),
    text_equals('To the order of'),
    text_equals('Void', tolerance=0),
    text_equals('Watermark'),
    text_equals('Cents'),
    text_equals('Face', tolerance=0),
    text_equals('Background'))

is_check_number = all_hold(
    text_properties_are(
        length={'at_least': 5, 'at_most': 10},
        legal_chars=NUMBERS+CHECK_NUMBER_SYMBOLS,
        tolerance=0, taper=2),
    line_count_is({1:1,2:0}))

is_routing_number = text_properties_are(length={'at_least': 9, 'at_most': 9},
  legal_chars=NUMBERS+CHECK_NUMBER_SYMBOLS+MICR_SYMBOLS,tolerance=1, taper=3)

is_account_number = text_properties_are(length={'at_least': 6, 'at_most': 12},
    legal_chars=NUMBERS+CHECK_NUMBER_SYMBOLS+MICR_SYMBOLS,tolerance=1, taper=3)

is_payor = all_hold(
    is_entire_phrase,
    nothing_between_left_edge,
    text_properties_are(
        length={'at_least': 4},
        legal_chars=LETTERS+PAYOR_SYMBOLS,
        tolerance=0, taper=1),
    all_hold(*(text_does_not_contain_substring(word)
        for word in CHECK_WORDS)),
    is_in_page_region((0.0, 0.5)),
    is_oriented_horizontally())

is_payee = all_hold(
    text_properties_are(
        length={'at_least': 4},
        legal_chars=LETTERS+PAYOR_SYMBOLS,
        tolerance=0, taper=1),
    is_in_page_region((0.0, 0.7)),
    text_does_not_contain_substring('Thousand'),
    text_does_not_contain_substring('Hundred'),
    text_does_not_contain_substring('Cents'),
    text_does_not_contain_substring('Dollars'),
    text_does_not_contain_substring('Document'),
    text_does_not_contain_substring('Date'),
    text_does_not_contain_substring('Amount'),
    text_does_not_contain_substring('Order'),
    text_does_not_contain_substring('Attn'))

is_check_address = all_hold(
    line_count_is(score_dict={1:0.5, 2:1.0, 3:0.5, 4:0}),
    any_holds(*(non_fatal(text_has_substring(word), 0.7)
        for word in STREET_WORDS)),
    any_holds(*(text_has_substring(word)
        for word in STATE_ABBREVS)),
    all_hold(*(text_does_not_contain_substring(word)
        for word in CHECK_WORDS)))


# Layouts
# =======

ltr_amount = extract(
  is_amount('amount'),
  is_amount_label('amount_label'),
  is_left_to_right_label_value_pair('amount_label', 'amount')) \
      .with_name('ltr amount')

top_down_amount = extract(
  is_amount('amount'),
  is_amount_label('amount_label'),
  is_top_down_label_value_pair('amount_label', 'amount')) \
      .with_name('top-down amount')

no_label_amount = extract(
  penalize(all_hold(
    is_amount,
    is_in_page_region(x_range=(0.6,1.0))), 0.7)('amount')) \
        .with_name('no-label amount')

ltr_date = extract(
  is_date('date'),
  is_date_label('date_label'),
  is_left_to_right_label_value_pair('date_label', 'date')) \
      .with_name('ltr date')

top_down_date = extract(
  is_date('date'),
  is_date_label('date_label'),
  is_top_down_label_value_pair('date_label', 'date')) \
      .with_name('top-down date')

bottom_up_date = extract(
  is_date('date'),
  is_date_label('date_label'),
  penalize(is_top_down_label_value_pair)('date', 'date_label'))

no_label_date = extract(
  non_fatal(penalize(all_hold(
    is_check_date,
    is_in_page_region(x_range=(0.7,1.0))), 0.7), 0.2)('date')) \
        .with_name('no-label date')

ltr_check_number = extract(
  is_check_number('check_number'),
  is_check_number_label('check_number_label'),
  is_left_to_right_label_value_pair('check_number_label', 'check_number')) \
      .with_name('ltr check_number')

top_down_check_number = extract(
  is_check_number('check_number'),
  is_check_number_label('check_number_label'),
  is_top_down_label_value_pair('check_number_label', 'check_number')) \
      .with_name('top-down check_number')

bottom_up_check_number = extract(
  is_check_number('check_number'),
  is_check_number_label('check_number_label'),
  penalize(is_top_down_label_value_pair)('check_number', 'check_number_label'))

no_label_check_number = extract(
  penalize(all_hold(
    is_check_number,
    is_in_page_region(x_range=(0.8,1.0))), 0.7)('check_number')) \
        .with_name('no-label check number')


# Long tail
# =========

long_tail_date = pick_best(ltr_date, top_down_date,
  bottom_up_date, no_label_date) \
    .with_name('long tail date')

long_tail_amount = pick_best(ltr_amount, top_down_amount, no_label_amount) \
    .with_name('long tail amount')

long_tail_check_number = pick_best(
  ltr_check_number, top_down_check_number, no_label_check_number,
  bottom_up_check_number) \
      .with_name('long tail check number')

check_anchor_node = extract(is_check_anchor('check_anchor')) \
    .with_name('long tail check anchor')

long_tail_pay_details = extract(
  is_pay_to_label('pay_to_label'),
  is_payor('payor'),
  is_payee('payee'),
  non_fatal(is_entire_phrase, 0.7)('payee'),
  non_fatal(empty_line_above, 0.75)('payee'),
  is_check_address('payee_address'),
  is_check_address('payor_address'),
  are_arranged(Direction.TOP_DOWN)('payor', 'pay_to_label'),
  any_holds(
      all_hold(
          are_arranged(Direction.LEFT_TO_RIGHT),
          nothing_between_horizontally,
          are_aligned(AlignmentLine.BOTTOMS, tolerance=3, taper=2)),
      all_hold(
        one_line_above,
        nothing_between_vertically),
  )('pay_to_label', 'payee'),
  are_arranged(Direction.TOP_DOWN)('payor', 'payee'),
  are_arranged(Direction.TOP_DOWN)('payor_address', 'payee_address'),
  column('payee', 'payee_address'),
  one_line_above('payor', 'payor_address'),
  nothing_between_vertically('payor', 'payor_address'),
  any_holds(
      are_aligned(AlignmentLine.HORIZONTAL_MIDLINES, tolerance=2, taper=3.5),
      are_aligned(AlignmentLine.LEFT_SIDES, tolerance=2, taper=3.5))
          ('payor', 'payor_address'),
)

extra_rules = (
  *tuple(are_disjoint(a, b) for a, b in pairs(check_fields)),
  *entity_strings_are_pairwise_disjoint('amount', 'check_number', 'date'),
  non_fatal(are_arranged(Direction.TOP_DOWN), 0.5)('check_number', 'amount'),
)

top_check_rules = tuple(chain(extra_rules,
  (is_in_pixel_page_region(800, Direction.TOP_DOWN)(field)
      for field in ('check_anchor', 'payor', 'pay_to_label', 'payee')),
  (non_fatal(is_in_pixel_page_region(800, Direction.TOP_DOWN), 0.8)(field)
      for field in ('date', 'amount'))))

bottom_check_rules = tuple(chain(extra_rules,
  (is_in_pixel_page_region(1000, Direction.BOTTOM_UP)(field)
      for field in ('check_anchor', 'payor', 'pay_to_label', 'payee')),
  (non_fatal(is_in_pixel_page_region(1000, Direction.BOTTOM_UP), 0.8)(field)
      for field in ('date', 'amount'))))

long_tail_top = reduce(combine, (check_anchor_node, long_tail_date,
    long_tail_amount, long_tail_check_number, long_tail_pay_details,
    )).with_extra_rules(*top_check_rules) \
        .with_name('long tail top check')

long_tail_bottom = reduce(combine, (check_anchor_node, long_tail_date,
    long_tail_amount, long_tail_check_number, long_tail_pay_details,
    )).with_extra_rules(*bottom_check_rules) \
        .with_name('long tail bottom check')

root = pick_best(long_tail_top, long_tail_bottom) \
    .with_name('long tail top/bottom')

"""
 WIP Notes:
 - Payor gets messed up by sideways tiny writing on side.
 - By semi-forcing the date/amount to be on the check, we're missing many
      "accidental" correct answers, and opening ourselves up to many more ocr
      errors. However, stops us from getting incorrect amount/date from invoice.
 - Some checks have different corner check numbers and check control numbers
       (most have same) eg. 84,85.
"""

# main
# ====

if __name__ == '__main__':
  bp_cli_main(root, Config(num_samples=100))
