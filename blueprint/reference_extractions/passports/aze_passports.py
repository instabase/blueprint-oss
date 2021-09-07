#!/usr/bin/env python3

from bp import *

#  # Labels
#  # ======
#  
#  # This can be a label for the period gross pay (to the right of the label or
#  # below it, with no cross-labeling), or it can be a label for the gross pay
#  # row/column in a table, with period/YTD columns/rows.
#  
#  is_restrictive_gross_pay_label = any_holds(
#    text_equals('Gross earnings'),
#    text_equals('Gross pay'),
#    text_equals('Gross wages'),
#    text_equals('Gross (less imputed)'),
#    text_equals('Total earnings'),
#    text_equals('Total compensation'),
#    text_equals('Total wages', tolerance=0),
#    text_equals('Total pay'),
#    text_equals('Total gross'),
#    text_equals('Salary & other income'))
#  
#  # The label for a gross pay row/column in a table which has period/YTD
#  # columns/rows.
#  is_gross_pay_label = any_holds(
#    is_restrictive_gross_pay_label,
#    all_hold(
#      text_equals('Earnings'),
#      is_entire_phrase),
#    all_hold(
#      text_equals('Gross'),
#      is_entire_phrase))
#  
#  # In some layouts, allow "Total" as the gross pay label.
#  is_permissive_gross_pay_label = any_holds(
#    is_gross_pay_label,
#    all_hold(
#      text_equals('Total'),
#      is_entire_phrase),
#    all_hold(
#      text_equals('Totals'),
#      is_entire_phrase),
#    text_equals('Total:'),
#    text_equals('Totals:'))
#  
#  # This is the label for a period gross pay label/value pair which is not in a
#  # table -- a label which is above or to the left of its value, and that's the
#  # only label the value has.
#  is_period_gross_pay_label = any_holds(
#    is_restrictive_gross_pay_label,
#    text_equals('Cur. earnings'),
#    text_equals('Current gross'),
#    text_equals('Current earnings'))
#  
#  # This is the label for a YTD gross pay label/value pair which is not in a
#  # table, similar to is_period_gross_pay_label.
#  is_ytd_gross_pay_label = any_holds(
#    text_equals('Year to date gross'),
#    text_equals('Gross year-to-date'),
#    text_equals('YTD earnings'),
#    text_equals('YTD total gross'),
#    text_equals('Y.T.D earnings'),
#    text_equals('YTD gross'),
#    text_equals('Y.T.D. gross'),
#    text_equals('Gross YTD'))
#  
#  # This is the label for a net pay row/column in a table which has period/YTD
#  # columns/rows.
#  is_net_pay_label = any_holds(
#    text_equals('Net pay', tolerance=0), # Don't catch 'OT pay', 'Reg pay'.
#    text_equals('Net pay:'),
#    text_equals('Net check'),
#    text_equals('Net check:'),
#    text_equals('Net earnings'),
#    text_equals('**NET EARNINGS**'), # Hacky.
#    text_equals('Net deposit'),
#    text_equals('Total net pay'),
#    text_equals('Equals net pay'),
#    text_equals('Total net'),
#    text_equals('Direct deposit'),
#    text_equals('Direct deposit total'),
#    text_equals('Net direct deposit'),
#    text_equals('Take home'),
#    text_equals('Net pay to checking'))
#  
#  # The label for a period net pay label/value pair which is not in a table.
#  is_period_net_pay_label = any_holds(
#    is_net_pay_label,
#    text_equals('Current net pay'),
#    text_equals('Check amount'),
#    text_equals('Net wages/period'))
#  
#  # The label for a YTD net pay label/value pair which is not in a table.
#  is_ytd_net_pay_label = any_holds(
#    text_equals('Year to date net pay'),
#    text_equals('YTD net pay'),
#    text_equals('Net year-to-date'),
#    text_equals('Net pay year-to-date:'),
#    text_equals('Net YTD'),
#    text_equals('Net pay Y.T.D'),
#    text_equals('Net pay Y-T-D'),
#    text_equals('Net wages YTD'))
#  
#  # The label for a period row/column in a table which has net/gross columns/rows.
#  is_period_pay_label = any_holds(
#    text_equals('P/P', tolerance=0, taper=0),
#    text_equals('Current'),
#    text_equals('Current pay'),
#    text_equals('Current period'),
#    text_equals('Current earnings/ded'),
#    text_equals('Current totals:'),
#    text_equals('Current ($)'),
#    text_equals('This period'),
#    text_equals('This check'),
#    text_equals('This period ($)'),
#    text_equals('Amount'))
#  
#  # The label for a YTD row/column in a table which has net/gross columns/rows.
#  is_ytd_pay_label = any_holds(
#    text_equals('Year to date'),
#    text_equals('YR TO DATE'),
#    text_equals('Year-to-date'),
#    text_equals('Year-to-date totals:'),
#    text_equals('Year-to-date earnings/ded'),
#    text_equals('Y-T-D'),
#    text_equals('Y.T.D. amount'),
#    all_hold(
#      text_equals('YTD', text_comparison_flags=TextComparisonFlags.CASE_SENSITIVE, tolerance=0, taper=1),
#      is_entire_phrase),
#    text_equals('YTD:', tolerance=0, taper=0),
#    text_equals('YTD amount'),
#    text_equals('To date', tolerance=0, taper=1),
#    text_equals('YTD ($)'),
#    text_equals('Calendar'))
#  
#  # This is the text that signifies an earnings table.
#  is_earnings_label = any_holds(
#    text_equals('Earnings'),
#    text_equals('Wages'),
#    text_equals('Current earnings'),
#    text_equals('Current hours & earnings'),
#    text_equals('Hours and earnings'),
#    text_equals('Gross earnings'))
#  
#  # This is a "Description" label in the header of an earnings table.
#  is_description_label = any_holds(
#    text_equals('Description'),
#    text_equals('Type'),
#    text_equals('Code'))
#  
#  # A label for a pay period begin date.
#  is_period_begin_label = any_holds(
#    text_equals('Period Beginning:'),
#    text_equals('Period Beginning Date'),
#    text_equals('Period Begin'),
#    text_equals('Period Start'),
#    text_equals('Period Starting:'),
#    text_equals('Period Start Date'),
#    text_equals('Pay Begin Date:'),
#    text_equals('Check stub for the period:'),
#    text_equals('Pay period start'),
#    text_equals('Pay period begin'),
#    text_equals('Start period'),
#    text_equals('Pay BegDt'),
#    text_equals('Pay Start'))
#  
#  # A label for a pay period ending date.
#  is_period_end_label = any_holds(
#    text_equals('Period Ending:'),
#    text_equals('Period Ending Date'),
#    text_equals('Period End:'),
#    text_equals('Period End Date'),
#    text_equals('Pay End Date:'),
#    text_equals('END DATE'),
#    text_equals('Pay period end'),
#    text_equals('Pay EndDt'),
#    text_equals('Pay End'),
#    text_equals('End period'))
#  
#  # A label for a pay period date range.
#  is_pay_period_label = any_holds(
#    # text_equals('Period:'),
#    # text_equals('Paydate:'),
#    text_equals('Pay Period:'),
#    text_equals('Pay Period from'),
#    text_equals('Period Dates'),
#    text_equals('For period:'),
#    text_equals('Pay stub for period:'),
#    text_equals('Inclusive Dates:'),
#    text_equals('Period Beg/End:'))
#  
#  # A label for the pay date.
#  is_pay_date_label = any_holds(
#    # text_equals('Date:'),
#    text_equals('Check Date:'),
#    text_equals('Pay Date:'),
#    text_equals('Payment Date'),
#    text_equals('Deposit Date'),
#    text_equals('Paid Date:'),
#    text_equals('Advice Date:'),
#    text_equals('with a pay date of'))
#  
#  # Long tail
#  # =========
#  
#  ltr_period_begin_date = extract(
#    is_period_begin_label('period_begin_label'),
#    is_date('period_begin_date'),
#    is_left_to_right_label_value_pair('period_begin_label', 'period_begin_date'),
#  ).with_name('LTR period begin date')
#  
#  ltr_period_end_date = extract(
#    is_period_end_label('period_end_label'),
#    is_date('period_end_date'),
#    is_left_to_right_label_value_pair('period_end_label', 'period_end_date'),
#  ).with_name('LTR period end date')
#  
#  ltr_pay_date = extract(
#    is_pay_date_label('pay_date_label'),
#    is_date('pay_date'),
#    is_left_to_right_label_value_pair('pay_date_label', 'pay_date'),
#  ).with_name('LTR pay date')
#  
#  top_down_period_begin_date = extract(
#    is_period_begin_label('period_begin_label'),
#    is_date('period_begin_date'),
#    is_top_down_label_value_pair('period_begin_label', 'period_begin_date'),
#  ).with_name('top-down period begin date')
#  
#  top_down_period_end_date = extract(
#    is_period_end_label('period_end_label'),
#    is_date('period_end_date'),
#    is_top_down_label_value_pair('period_end_label', 'period_end_date'),
#  ).with_name('top-down period end date')
#  
#  top_down_pay_date = extract(
#    is_pay_date_label('pay_date_label'),
#    is_date('pay_date'),
#    is_top_down_label_value_pair('pay_date_label', 'pay_date'),
#  ).with_name('top-down pay date')
#  
#  pay_period_date_range = extract(
#    is_pay_period_label('pay_period_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    row('pay_period_label', 'period_begin_date', 'period_end_date'),
#    nothing_between_horizontally('pay_period_label', 'period_begin_date'),
#    # The two dates may have the word "to", or a dash, between them.
#  )
#  
#  ltr_period_gross_pay = extract(
#    is_period_gross_pay_label('period_gross_pay_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_left_to_right_label_value_pair('period_gross_pay_label', 'period_gross_pay'),
#  ).with_name('LTR period gross pay')
#  
#  ltr_period_net_pay = extract(
#    is_period_net_pay_label('period_net_pay_label'),
#    is_dollar_amount('period_net_pay'),
#    is_left_to_right_label_value_pair('period_net_pay_label', 'period_net_pay'),
#  ).with_name('LTR period net pay')
#  
#  one_line_down_period_net_pay = extract(
#    is_period_net_pay_label('period_net_pay_label'),
#    is_dollar_amount('period_net_pay'),
#    all_hold(is_immediate_header, heads_tabular_entry)
#      ('period_net_pay_label', 'period_net_pay'),
#  ).with_name('one line down period net pay')
#  
#  ltr_ytd_gross_pay = extract(
#    is_ytd_gross_pay_label('ytd_gross_pay_label'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_left_to_right_label_value_pair('ytd_gross_pay_label', 'ytd_gross_pay'),
#  ).with_name('LTR YTD gross pay')
#  
#  ltr_ytd_net_pay = extract(
#    is_ytd_net_pay_label('ytd_net_pay_label'),
#    is_dollar_amount('ytd_net_pay'),
#    is_left_to_right_label_value_pair('ytd_net_pay_label', 'ytd_net_pay'),
#  ).with_name('LTR YTD net pay')
#  
#  top_down_period_gross_pay = extract(
#    is_period_gross_pay_label('period_gross_pay_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_top_down_label_value_pair('period_gross_pay_label', 'period_gross_pay'),
#  ).with_name('top-down period gross pay')
#  
#  top_down_period_net_pay = extract(
#    is_period_net_pay_label('period_net_pay_label'),
#    is_dollar_amount('period_net_pay'),
#    is_top_down_label_value_pair('period_net_pay_label', 'period_net_pay'),
#  ).with_name('top-town period net pay')
#  
#  top_down_ytd_gross_pay = extract(
#    is_ytd_gross_pay_label('ytd_gross_pay_label'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_top_down_label_value_pair('ytd_gross_pay_label', 'ytd_gross_pay'),
#  ).with_name('top-down YTD gross pay')
#  
#  top_down_ytd_net_pay = extract(
#    is_ytd_net_pay_label('ytd_net_pay_label'),
#    is_dollar_amount('ytd_net_pay'),
#    is_top_down_label_value_pair('ytd_net_pay_label', 'ytd_net_pay'),
#  ).with_name('top-down YTD net pay')
#  
#  def double_labeled_value(
#      label1: Field, label1_description: Predicate, label2: Field,
#      label2_description: Predicate, value: Field,
#      value_description: Predicate) -> Node:
#    # FIXME: This is much nicer to spell if we have GHI #102.
#  
#    """A label-label-value triple, where the labels are to the left of and above
#    the value, in one configuration or the other."""
#    x1 = extract(
#      label1_description(label1),
#      label2_description(label2),
#      value_description(value),
#  
#      tabular_row(label1, value),
#      tabular_column(label2, value),
#    ).with_name(
#      f'left_and_upper_labeled_value('
#      f'left_label={label1}, '
#      f'upper_label={label2}, '
#      f'value={value})')
#    x2 = extract(
#      label1_description(label1),
#      label2_description(label2),
#      value_description(value),
#  
#      tabular_row(label2, value),
#      tabular_column(label1, value),
#    ).with_name(
#      f'left_and_upper_labeled_value('
#      f'left_label={label2}, '
#      f'upper_label={label1}, '
#      f'value={value})')
#  
#    return pick_best(x1, x2).with_name(
#      f'double_labeled_value({label1}, {label2}, {value})')
#  
#  period_gross_pay_triple = double_labeled_value(
#    'DLV_period_gross_pay_label', is_gross_pay_label,
#    'DLV_gross_pay_period_label', is_period_pay_label,
#    'period_gross_pay', is_dollar_amount)
#  
#  period_net_pay_triple = double_labeled_value(
#    'DLV_period_net_pay_label', is_net_pay_label,
#    'DLV_net_pay_period_label', is_period_pay_label,
#    'period_net_pay', is_dollar_amount)
#  
#  ytd_gross_pay_triple = double_labeled_value(
#    'DLV_ytd_gross_pay_label', is_gross_pay_label,
#    'DLV_gross_pay_ytd_label', is_ytd_pay_label,
#    'ytd_gross_pay', is_dollar_amount)
#  
#  ytd_net_pay_triple = double_labeled_value(
#    'DLV_ytd_net_pay_label', is_net_pay_label,
#    'DLV_net_pay_ytd_label', is_ytd_pay_label,
#    'ytd_net_pay', is_dollar_amount)
#  
#  simple_earnings_table = extract(
#    is_earnings_label('earnings_label'),
#    is_period_pay_label('period_pay_label'),
#    is_ytd_pay_label('ytd_pay_label'),
#    is_permissive_gross_pay_label('gross_pay_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    row('earnings_label', 'period_pay_label', 'ytd_pay_label'),
#    row('gross_pay_label', 'period_gross_pay', 'ytd_gross_pay'),
#    no_words_between_horizontally('gross_pay_label', 'period_gross_pay'),
#    no_words_between_horizontally('gross_pay_label', 'ytd_gross_pay'),
#    left_aligned_column('earnings_label', 'gross_pay_label'),
#    right_aligned_column('period_pay_label', 'period_gross_pay'),
#    no_words_between_vertically('period_pay_label', 'period_gross_pay'),
#    right_aligned_column('ytd_pay_label', 'ytd_gross_pay'),
#    no_words_between_vertically('ytd_pay_label', 'ytd_gross_pay'),
#  ).with_name('earnings table, label in header row')
#  
#  headed_earnings_table = extract(
#    is_earnings_label('earnings_label'),
#    is_description_label('description_label'),
#    is_period_pay_label('current_amount_label'),
#    is_ytd_pay_label('ytd_amount_label'),
#    is_permissive_gross_pay_label('total_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_immediate_header('earnings_label', 'description_label'),
#    is_immediate_header('earnings_label', 'current_amount_label'),
#    is_immediate_header('earnings_label', 'ytd_amount_label'),
#    row('description_label', 'current_amount_label', 'ytd_amount_label'),
#    row('total_label', 'period_gross_pay', 'ytd_gross_pay'),
#    no_words_between_horizontally('total_label', 'period_gross_pay'),
#    no_words_between_horizontally('total_label', 'ytd_gross_pay'),
#    tabular_column('current_amount_label', 'period_gross_pay'),
#    tabular_column('ytd_amount_label', 'ytd_gross_pay'),
#  ).with_name('earnings table, label above header row')
#  
#  double_headed_period_earnings_table = extract(
#    any_holds(
#      is_earnings_label,
#      text_equals('--Current earnings--'),
#      text_equals('Current earnings detail'),
#      text_equals('Current hours & earnings'),
#      text_equals('Pay period hours and earnings'),
#      all_hold(
#        text_equals('Current'),
#        is_entire_phrase))
#          ('current_earnings_label'),
#    any_holds(
#      text_equals('Amount'),
#      text_equals('Earnings'),
#      text_equals('Total'))
#        ('current_amount_label'),
#    is_permissive_gross_pay_label('current_total_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_immediate_header('current_earnings_label', 'current_amount_label'),
#    tabular_row('current_total_label', 'period_gross_pay'),
#    tabular_column('current_amount_label', 'period_gross_pay'),
#  ).with_name('current pay period double-headed earnings table')
#  
#  double_headed_ytd_earnings_table = extract(
#    any_holds(
#      text_equals('Y-T-D earnings'),
#      text_equals('Year-to-date'), # This is too generic...
#      text_equals('Year to date hours & earnings'),
#      text_equals('Earnings YTD'),
#      text_equals('YTD earnings'))
#        ('ytd_earnings_label'),
#    any_holds(
#      text_equals('YTD Amount'),
#      text_equals('Amount'),
#      text_equals('Earnings'),
#      all_hold(
#        text_equals('YTD'),
#        is_entire_phrase))
#          ('ytd_amount_label'),
#    any_holds(
#      is_permissive_gross_pay_label,
#      text_equals('Total YTD:'))
#        ('ytd_total_label'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_immediate_header('ytd_earnings_label', 'ytd_amount_label'),
#    tabular_row('ytd_total_label', 'ytd_gross_pay'),
#    tabular_column('ytd_amount_label', 'ytd_gross_pay'),
#  ).with_name('ytd double-headed earnings table')
#  
#  long_tail_period_gross_pay = pick_best(
#    ltr_period_gross_pay,
#    top_down_period_gross_pay,
#    period_gross_pay_triple,
#    double_headed_period_earnings_table,
#  ).with_name('long tail period gross pay')
#  
#  long_tail_period_net_pay = pick_best(
#    ltr_period_net_pay,
#    top_down_period_net_pay,
#    period_net_pay_triple,
#    one_line_down_period_net_pay,
#  ).with_name('period net pay')
#  
#  long_tail_ytd_gross_pay = pick_best(
#    ltr_ytd_gross_pay,
#    top_down_ytd_gross_pay,
#    ytd_gross_pay_triple,
#    double_headed_ytd_earnings_table,
#  ).with_name('ytd gross pay')
#  
#  long_tail_ytd_net_pay = pick_best(
#    ltr_ytd_net_pay,
#    top_down_ytd_net_pay,
#    ytd_net_pay_triple,
#  ).with_name('ytd net pay')
#  
#  long_tail_gross_pay_singletons = combine(
#    long_tail_period_gross_pay,
#    long_tail_ytd_gross_pay,
#    allowed_to_overlap=[
#      # If we get both the period and YTD gross pay using double-labeled-value
#      # structures, the "gross pay" label from the two structures may actually be
#      # the same entity in the document. Normally, combine() adds rules that its
#      # arguments don't overlap. Here we tell combine() that those fields may
#      # overlap, or be identical.
#      {'DLV_period_gross_pay_label',
#       'DLV_ytd_gross_pay_label'},
#    ],
#  ).with_name('singletons')
#  
#  long_tail_gross_pay = pick_best(
#    simple_earnings_table,
#    headed_earnings_table,
#    long_tail_gross_pay_singletons,
#  ).with_name('gross pay')
#  
#  long_tail_net_pay = combine(
#    long_tail_period_net_pay,
#    long_tail_ytd_net_pay,
#    allowed_to_overlap=[ # See above.
#      {'DLV_period_net_pay_label',
#       'DLV_ytd_net_pay_label'},
#    ],
#  ).with_name('net pay')
#  
#  long_tail_gross_net_pay = combine(
#    long_tail_gross_pay,
#    long_tail_net_pay,
#    allowed_to_overlap=[ # See above.
#      {'DLV_gross_pay_period_label',
#       'DLV_net_pay_period_label'},
#      # These two blocks are separate because, for example, the "period" label and
#      # the "YTD" label for the gross pay should still not overlap.
#      {'DLV_gross_pay_ytd_label',
#       'DLV_net_pay_ytd_label'},
#    ],
#  ).with_name('long tail gross/net pay')
#  
#  long_tail_period_begin_date = pick_best(
#    ltr_period_begin_date,
#    top_down_period_begin_date,
#  ).with_name('period begin')
#  
#  long_tail_period_ending_date = pick_best(
#    ltr_period_end_date,
#    top_down_period_end_date,
#  ).with_name('period end')
#  
#  long_tail_pay_period = pick_best(
#    combine(
#      long_tail_period_begin_date,
#      long_tail_period_ending_date,
#    ).with_name('separate pay period begin and ending dates'),
#    pay_period_date_range,
#  ).with_name('long tail period dates')
#  
#  long_tail_pay_date = pick_best(
#    ltr_pay_date,
#    top_down_pay_date,
#  ).with_name('pay date')
#  
#  long_tail_dates = combine(
#    long_tail_pay_period,
#    long_tail_pay_date,
#  ).with_name('long tail dates')
#  
#  long_tail = combine(
#    long_tail_gross_net_pay,
#    long_tail_dates,
#  ).with_name('long tail')
#  
#  # Templates
#  # =========
#  
#  paychex_left_to_right_net_pay = all_hold(
#    are_arranged(Direction.LEFT_TO_RIGHT, taper=2),
#    are_arranged(Direction.TOP_DOWN, min_distance=0, max_distance=1, taper=2))
#  
#  paychex = extract(
#    text_equals('EARNINGS')('earnings_label'),
#    text_equals('DESCRIPTION')('description_label'),
#    text_equals('THIS PERIOD ($)')('period_pay_label'),
#    text_equals('YTD ($)')('ytd_pay_label'),
#    text_equals('Gross Earnings')('gross_earnings_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    text_equals('NET PAY')('net_pay_label'),
#    is_dollar_amount('period_net_pay'),
#    is_dollar_amount('ytd_net_pay'),
#    text_equals('Pay Period:')('pay_period_label'),
#    text_equals('Check Date:')('check_date_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    is_date('pay_date'),
#    row('earnings_label', 'description_label', 'period_pay_label', 'ytd_pay_label'),
#    row('gross_earnings_label', 'period_gross_pay', 'ytd_gross_pay'),
#    paychex_left_to_right_net_pay('net_pay_label', 'period_net_pay'),
#    paychex_left_to_right_net_pay('net_pay_label', 'ytd_net_pay'),
#    row('period_net_pay', 'ytd_net_pay'),
#    left_aligned_column('earnings_label', 'net_pay_label'),
#    left_aligned_column('description_label', 'gross_earnings_label'),
#    right_aligned_column('period_pay_label', 'period_gross_pay', 'period_net_pay'),
#    right_aligned_column('ytd_pay_label', 'ytd_gross_pay', 'ytd_net_pay'),
#    is_left_to_right_label_value_pair('check_date_label', 'pay_date'),
#    row('pay_period_label', 'period_begin_date', 'period_end_date'),
#    nothing_between_horizontally('pay_period_label', 'period_begin_date'),
#  ).with_name('Paychex')
#  
#  intuit_top_down_right_aligned_within_2_lines = all_hold(
#    are_arranged(Direction.TOP_DOWN, max_distance=2, taper=2),
#    are_aligned(AlignmentLine.RIGHT_SIDES, tolerance=1, taper=5))
#  
#  intuit = extract(
#    text_equals('Earnings and Hours')('earnings_and_hours_label'),
#    text_equals('Current')('earnings_current_label'),
#    text_equals('YTD Amount')('earnings_ytd_label'),
#    text_equals('Taxes')('taxes_label'),
#    text_equals('Current')('taxes_current_label'),
#    text_equals('YTD Amount')('taxes_ytd_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    text_equals('Net Pay')('net_pay_label'),
#    is_dollar_amount('period_net_pay'),
#    is_dollar_amount('ytd_net_pay'),
#    text_equals('Pay Period:')('pay_period_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    text_equals('Pay Date:')('pay_date_label'),
#    is_date('pay_date'),
#    row('earnings_and_hours_label', 'earnings_current_label', 'earnings_ytd_label'),
#    row('period_gross_pay', 'ytd_gross_pay'),
#    row('taxes_label', 'taxes_current_label', 'taxes_ytd_label'),
#    row('net_pay_label', 'period_net_pay', 'ytd_net_pay'),
#    left_aligned_column('earnings_and_hours_label', 'net_pay_label'),
#    right_aligned_column('earnings_current_label', 'period_gross_pay'),
#    right_aligned_column('earnings_ytd_label', 'ytd_gross_pay'),
#    intuit_top_down_right_aligned_within_2_lines('period_gross_pay', 'taxes_current_label'),
#    intuit_top_down_right_aligned_within_2_lines('ytd_gross_pay', 'taxes_ytd_label'),
#    right_aligned_column('taxes_current_label', 'period_net_pay'),
#    right_aligned_column('taxes_ytd_label', 'ytd_net_pay'),
#    row('pay_period_label', 'period_begin_date', 'period_end_date'),
#    nothing_between_horizontally('pay_period_label', 'period_begin_date'),
#    is_left_to_right_label_value_pair('pay_date_label', 'pay_date'),
#  ).with_name('Intuit')
#  
#  summary_table = extract(
#    text_equals('SUMMARY')('summary_label'),
#    text_equals('Current')('summary_current_label'),
#    text_equals('YTD')('summary_ytd_label'),
#    text_equals('Total Pay')('summary_total_pay_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    text_equals('Period Beginning:')('period_begin_label'),
#    text_equals('Period Ending:')('period_end_label'),
#    text_equals('Pay Date:')('pay_date_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    is_date('pay_date'),
#    row('summary_label', 'summary_current_label', 'summary_ytd_label'),
#    row('summary_total_pay_label', 'period_gross_pay', 'ytd_gross_pay'),
#    tabular_column('summary_label', 'summary_total_pay_label'),
#    right_aligned_column('summary_current_label', 'period_gross_pay'),
#    right_aligned_column('summary_ytd_label', 'ytd_gross_pay'),
#    is_left_to_right_label_value_pair('period_begin_label', 'period_begin_date'),
#    is_left_to_right_label_value_pair('period_end_label', 'period_end_date'),
#    is_left_to_right_label_value_pair('pay_date_label', 'pay_date'),
#  ).with_name('summary table')
#  
#  summary_table_layout = combine(
#    summary_table,
#    ltr_period_net_pay,
#  ).with_name('summary table')
#  
#  ceridian_sloppy_top_down_right_aligned_very_close = all_hold(
#    are_arranged(Direction.TOP_DOWN, max_distance=0.75, taper=2),
#    are_aligned(AlignmentLine.RIGHT_SIDES, tolerance=5))
#  
#  ceridian_left_to_right_and_top_down = all_hold(
#    are_arranged(Direction.LEFT_TO_RIGHT, taper=0),
#    are_arranged(Direction.TOP_DOWN, taper=2))
#  
#  ceridian = extract(
#    text_equals('Amount')('ytd_upper_amount_label'),
#    text_equals('Amount')('current_upper_amount_label'),
#    text_equals('Amount')('current_lower_amount_label'),
#    text_equals('Amount')('ytd_lower_amount_label'),
#    text_equals('Current')('current_label'),
#    text_equals('YTD')('ytd_pay_label'),
#    text_equals('Earnings')('earnings_label'),
#    text_equals('Net Pay')('net_pay_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('period_net_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_dollar_amount('ytd_net_pay'),
#    text_equals('Pay Date:')('pay_date_label'),
#    is_date('pay_date'),
#    text_equals('Pay Period:')('pay_period_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    left_aligned_column('pay_date_label', 'pay_period_label'),
#    row('pay_date_label', 'pay_date'),
#    row('pay_period_label', 'period_begin_date', 'period_end_date'),
#    row('current_label', 'ytd_pay_label'),
#  
#    ceridian_left_to_right_and_top_down('current_label', 'current_upper_amount_label'),
#    ceridian_left_to_right_and_top_down('ytd_pay_label', 'ytd_upper_amount_label'),
#  
#    row('current_upper_amount_label', 'ytd_upper_amount_label'),
#    row('earnings_label', 'period_gross_pay', 'ytd_gross_pay'),
#  
#    ceridian_left_to_right_and_top_down('current_label', 'current_lower_amount_label'),
#    ceridian_left_to_right_and_top_down('ytd_pay_label', 'ytd_lower_amount_label'),
#  
#    row('current_lower_amount_label', 'ytd_lower_amount_label'),
#    row('net_pay_label', 'period_net_pay', 'ytd_net_pay'),
#  
#    left_aligned_column('earnings_label', 'net_pay_label'),
#  
#    nothing_between_vertically('current_upper_amount_label', 'period_gross_pay'),
#    nothing_between_vertically('ytd_upper_amount_label', 'ytd_gross_pay'),
#  
#    ceridian_sloppy_top_down_right_aligned_very_close
#      ('current_upper_amount_label', 'period_gross_pay'),
#    right_aligned_column('current_upper_amount_label', 'current_lower_amount_label'),
#    ceridian_sloppy_top_down_right_aligned_very_close
#      ('current_lower_amount_label', 'period_net_pay'),
#    right_aligned_column('period_gross_pay', 'period_net_pay'),
#  
#    ceridian_sloppy_top_down_right_aligned_very_close
#      ('ytd_upper_amount_label', 'ytd_gross_pay'),
#    right_aligned_column('ytd_upper_amount_label', 'ytd_lower_amount_label'),
#    ceridian_sloppy_top_down_right_aligned_very_close
#      ('ytd_lower_amount_label', 'ytd_net_pay'),
#    right_aligned_column('ytd_gross_pay', 'ytd_net_pay'),
#  ).with_name('Ceridian')
#  
#  paycor = extract(
#    text_equals('NET')('net_label'),
#    is_dollar_amount('period_net_pay'),
#    text_equals('TOTALS')('totals_label'),
#    is_dollar_amount('period_gross_pay'),
#    is_dollar_amount('ytd_gross_pay'),
#    is_dollar_amount('period_taxes'),
#    is_dollar_amount('ytd_taxes'),
#    text_equals('CURRENT $')('current_dollars_label'),
#    text_equals('YTD $')('ytd_dollars_label'),
#    text_equals('DEDUCTION')('deduction_label'),
#    text_equals('CURRENT $')('deduction_current_dollars_label'),
#    text_equals('YTD $')('deduction_ytd_dollars_label'),
#    text_equals('TAX')('tax_label'),
#    text_equals('CURRENT $')('tax_current_dollars_label'),
#    text_equals('YTD $')('tax_ytd_dollars_label'),
#  
#    text_equals('Check stub for the period')('period_begin_label'),
#    text_equals('to')('period_end_label'),
#    text_equals('with a pay date of')('pay_date_label'),
#    is_date('period_begin_date'),
#    is_date('period_end_date'),
#    is_date('pay_date'),
#    row('period_begin_label', 'period_begin_date'),
#    row('period_end_label', 'period_end_date'),
#    row('pay_date_label', 'pay_date'),
#    right_aligned_column('period_begin_label', 'period_end_label', 'pay_date_label'),
#    right_aligned_column('period_begin_date', 'period_end_date', 'pay_date'),
#  
#    row('current_dollars_label', 'ytd_dollars_label', 'deduction_label',
#        'deduction_current_dollars_label', 'deduction_ytd_dollars_label',
#        'tax_label', 'tax_current_dollars_label', 'tax_ytd_dollars_label'),
#    row('net_label', 'period_net_pay', 'totals_label', 'period_gross_pay',
#        'ytd_gross_pay', 'period_taxes', 'ytd_taxes'),
#    right_aligned_column('current_dollars_label', 'period_gross_pay'),
#    right_aligned_column('ytd_dollars_label', 'ytd_gross_pay'),
#    right_aligned_column('tax_current_dollars_label', 'period_taxes'),
#    right_aligned_column('tax_ytd_dollars_label', 'ytd_taxes'),
#  ).with_name('Paycor')
#  
#  # Business logic inequalities
#  # ---------------------------
#  
#  # Describe some business logic inequalities to validate that the numbers we are
#  # getting for the period/YTD gross/net pay values make sense.
#  
#  cmp_net_gross = all_hold(
#    sum_is_positive([1, -0.25], strict=False),
#    sum_is_positive([-1, 1.50], strict=False))
#  
#  cmp_period_ytd = all_hold(
#    sum_is_positive([1, -0.01], strict=False),
#    sum_is_positive([-1, 5.00], strict=False))
#  
#  business_logic_inequalities = (
#    cmp_net_gross     ('period_net_pay',      'period_gross_pay'),
#    cmp_net_gross     ('ytd_net_pay',         'ytd_gross_pay'),
#    cmp_period_ytd    ('period_net_pay',      'ytd_net_pay'),
#    cmp_period_ytd    ('period_gross_pay',    'ytd_gross_pay'))
#  
#  # Core pay amounts and dates
#  # --------------------------
#  
#  root = pick_best(
#    paychex,
#    summary_table_layout,
#    intuit,
#    ceridian,
#    paycor,
#    long_tail,
#  ).with_extra_rules(*business_logic_inequalities)

aze = extract(
  # text_equals('Tip/Type')('type_label'),
  # text_equals('Olkenin kodu/Code of State')('state_label'),
  # text_equals('Pasportun nomrasi/Passport No')('num_label'),
  text_equals('Soyadi/Surname')('sn_label'),
  text_equals('Adi, atasinin adi/Given name, patronymic')('fn_label'),
  # text_equals('Vetendasligi/Nationality')('nation_label'),
  #1 text_equals('Doguldugu tarix/Date of birth')('dob_label'),
  # text_equals('Fardi identifikasiya nomrasi/Personal No')('personal_no_label'),
  # text_equals('Cinsi/Sex')('sex_label'),
  text_equals('Doguldugu yer/Place of birth')('pob_label'),
  # text_equals('Verilma tarixi/Date of issue')('doi_label'),
  # text_equals('Etibarliliq muddati/Date of expiry')('doe_label'),
  # text_equals('Pasportu veran orqan/Issuing authority')('auth_label'),

  #1 is_date('dob'),
  # is_date('doi'),
  # is_date('doe'),

  # text_equals('AZE')('state'),
  # is_top_down_label_value_pair('state_label', 'state'),
  # is_top_down_label_value_pair('num_label', 'num'),

  is_top_down_label_value_pair('sn_label', 'sn'),
  is_top_down_label_value_pair('fn_label', 'fn'),
  # is_top_down_label_value_pair('nation_label', 'nation'),

  #1 is_top_down_label_value_pair('dob_label', 'dob'),
  # is_top_down_label_value_pair('personal_no_label', 'personal_no'),
  # is_top_down_label_value_pair('sex_label', 'sex'),

  is_top_down_label_value_pair('pob_label', 'pob'),

  # is_top_down_label_value_pair('doi_label', 'doi'),
  # is_top_down_label_value_pair('doe_label', 'doe'),

  # is_top_down_label_value_pair('auth_label', 'auth'),



  # row('type_label', 'state_label', 'num_label'),
  # row('dob_label', 'personal_no_label', 'sex_label'),

  #row('doi_label', 'doe_label'),

  # left_aligned_column('sn_label' 'fn_label', 'dob_label'),
  # left_aligned_column('type_label', 'sn_label' 'fn_label', 'nation_label', 'dob_label', 'pob_label', 'doi_label', 'auth_label'),
  # left_aligned_column('personal_no_label', 'doe_label'),

  # row('state', 'num'),
).with_name('AZE')


# Run on CLI
# ----------

config = Config(num_samples=100)

if __name__ == '__main__':
  bp_cli_main(aze, config=config)
