#!/usr/bin/env python3

from bp import *

# Helper rules
# ============

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NUMBERS = '0123456789'

is_in_upper_right_corner = is_in_page_region(
  x_range=(0.5, 1), y_range=(0, 0.25))
is_in_upper_left_corner = is_in_page_region(
  x_range=(0, 0.5), y_range=(0, 0.25))
is_in_upper_half = is_in_page_region(
                    y_range=(0, 0.5))
is_in_bottom_third_of_page = is_in_page_region(
                    y_range=(0.6, 1))
is_in_ports_and_vessels_region = is_in_page_region(
                    y_range=(0.2, 0.5))
is_on_left_side = is_in_page_region(
  x_range=(0, 0.5))
is_in_left_center_of_page = is_in_page_region(
  x_range=(0, 0.5), y_range=(0.2, 0.5))

# A "reference number" is a BOL number, a booking number, etc.
is_reference_number = text_properties_are(
  length={'at_least': 9, 'at_most': 16},
  legal_chars=LETTERS + NUMBERS + '/',
  max_char_proportions=[{'chars': LETTERS, 'proportion': 0.5}],
  max_char_counts=[{'chars': '/', 'count': 2}])

is_bol_address = line_count_is(score_dict={
  1: 0,
  3: 0.75,
  4: 0.8,
  5: 0.85,
  6: 1,
  7: 0,
})

is_label_address_pair = all_hold(
    top_down_pair(max_distance=3, taper=1),
    left_aligned_pair(tolerance=3, taper=3),
    no_words_between_vertically)

is_port_or_vessel = all_hold(
    is_entire_phrase,
    is_in_ports_and_vessels_region,
    text_properties_are(length={'at_most': 50}))

BOL_label_value_pair = all_hold(
    top_down_pair(max_distance=1, taper=1),
    left_aligned_pair(tolerance=3, taper=10))

is_top_down_label_value_pair = all_hold(
    top_down_pair(),
    nothing_between_vertically,
    any_holds(
      right_aligned_pair(),
      left_aligned_pair()))

# Document parts
# ==============

BOL_number = extract(
  text_is_one_of(('Bill of lading number',
              'Bill of lading no.',
              'Cargo receipt no.',
              'B/L number',
              'B/L no.',
              'MTD no.',
              'Waybill number',
              'Waybill no.',
              'Document no.',
              'FBL:'),
    text_comparison_flags=TextComparisonFlags.CASE_SENSITIVE,
    tolerance=0, taper=2)
      ('BOL_number_label'),
  is_in_upper_right_corner('BOL_number_label'),
  is_reference_number('BOL_number'),
  is_in_upper_right_corner('BOL_number'),
  any_holds(
    all_hold(
      left_to_right_pair(max_distance=10, taper=10),
      bottom_aligned_pair(tolerance=1.5)),
    all_hold(
      top_down_pair(max_distance=1.3, taper=1.3),
      left_aligned_pair(tolerance=2, taper=10))
    )('BOL_number_label', 'BOL_number'),
)

booking_number = extract(
  text_equals('Booking no')('booking_number_label'),
  is_reference_number('booking_number'),
  is_in_upper_right_corner('booking_number_label'),
  is_in_upper_right_corner('booking_number'),
  is_top_down_label_value_pair('booking_number_label', 'booking_number'),
)

shipper = extract(
  text_is_one_of(('Consignor',
              'Shipper',
              'Shipper/exporter',
              'Consignor/shipper'))
    ('shipper_label'),
  is_bol_address('shipper'),
  is_in_upper_left_corner('shipper'),
  is_label_address_pair('shipper_label', 'shipper'),
)

consignee = extract(
  text_equals('Consignee')('consignee_label'),
  any_holds(
    is_bol_address,
    text_equals('TO ORDER', tolerance=0),
    text_has_substring('TO THE ORDER OF ', tolerance=0))('consignee'),
  is_in_upper_left_corner('consignee_label'),
  is_in_upper_left_corner('consignee'),
  is_label_address_pair('consignee_label', 'consignee'),
)

notify = extract(
  text_is_one_of(('Notify1', 'Notify'))('notify_label'),
  is_in_upper_half('notify_label'),
  is_in_upper_half('notify'),
  is_bol_address('notify'),
  is_label_address_pair('notify_label', 'notify'),
)

also_notify = extract(
  text_is_one_of(('Also notify',
                'Notify2',
                'Also notify party',
                'Also notify parties'))
    ('also_notify_label'),
  is_bol_address('also_notify'),
  is_in_upper_half('also_notify_label'),
  is_in_upper_half('also_notify'),
  is_label_address_pair('also_notify_label', 'also_notify'),
)

port_of_loading = extract(
  text_equals('Port of loading')('port_of_loading_label'),
  is_port_or_vessel('port_of_loading'),
  BOL_label_value_pair('port_of_loading_label', 'port_of_loading'),
)

port_of_discharge = extract(
  text_equals('Port of discharge')('port_of_discharge_label'),
  is_port_or_vessel('port_of_discharge'),
  BOL_label_value_pair('port_of_discharge_label', 'port_of_discharge'),
)

place_of_delivery = extract(
  text_is_one_of(('Port of delivery', 'Place of delivery'))('place_of_delivery_label'),
  is_in_left_center_of_page('place_of_delivery_label'),
  is_port_or_vessel('place_of_delivery'),
  BOL_label_value_pair('place_of_delivery_label', 'place_of_delivery'),
)

place_of_receipt = extract(
  text_equals('Place of receipt')('place_of_receipt_label'),
  is_port_or_vessel('place_of_receipt'),
  BOL_label_value_pair('place_of_receipt_label', 'place_of_receipt'),
)

vessel = extract(
  text_is_one_of(('Vessel',
              'Vessel(s)',
              'Export carrier',
              'Ocean vessel',
              'Ocean vessel/voy. no'))
    ('vessel_label'),
  is_port_or_vessel('vessel'),
  is_on_left_side('vessel'),
  any_holds(
    is_one_line,
    is_two_lines)('vessel'),
  BOL_label_value_pair('vessel_label', 'vessel'),
)

country_of_origin = extract(
    text_is_one_of(('Point and country of origin',
                  'Country of origin'))
      ('country_of_origin_label'),
  is_port_or_vessel('country_of_origin'),
  BOL_label_value_pair('country_of_origin_label', 'country_of_origin'),

  top_down_pair(max_distance=0.75, taper=0.5)
    ('country_of_origin_label', 'country_of_origin'),
)

ship_date = extract(
  text_is_one_of(('Shipped on board',
              'Laden on board',
              'Place B/L issued',
              'Date of issue'))
    ('ship_date_label'),
  is_in_bottom_third_of_page('ship_date_label'),
  is_date('ship_date'),
  is_in_bottom_third_of_page('ship_date'),
  any_holds(
    all_hold(
      left_to_right_pair(),
      bottom_aligned_pair(
        tolerance=1, taper=0.5)),
    top_down_pair(
      min_distance=-0.5, taper=0.5))('ship_date_label', 'ship_date'),
)

# main
# ====

bill_of_lading = combine(
  BOL_number,
  booking_number,
  shipper,
  consignee,
  notify,
  also_notify,
  port_of_loading,
  port_of_discharge,
  place_of_delivery,
  place_of_receipt,
  country_of_origin,
  vessel,
  ship_date,
)

if __name__ == '__main__':
  bp_cli_main(bill_of_lading)
