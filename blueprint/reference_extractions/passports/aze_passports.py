#!/usr/bin/env python3

from bp import *

sn = extract(
  text_equals('Soyadi/Surname')('sn_label'),
  is_top_down_label_value_pair('sn_label', 'sn')
)

fn = extract(
  text_equals('Adi, atasinin adi/Given name, patronymic', taper=4)('fn_label'),
  is_top_down_label_value_pair('fn_label', 'fn')
)

pob = extract(
  text_equals('Doguldugu yer/Place of birth', taper=8)('pob_label'),
  is_top_down_label_value_pair('pob_label', 'pob')
)

dob = extract(
  text_equals('Doguldugu tarix/Date of birth', taper=4)('dob_label'),
  is_date('dob'),
  is_top_down_label_value_pair('dob_label', 'dob')
)

doe = extract(
  is_date('doe'),
  is_top_down_label_value_pair('doe_label', 'doe'),
  text_equals('Etibarliliq muddati/Date of expiry', taper=4)('doe_label')
)

doi  = extract(
  text_equals('Verilma tarixi/Date of issue', taper=4)('doi_label'),
  is_date('doi'),
  is_top_down_label_value_pair('doi_label', 'doi')
)

sex = extract(
  is_top_down_label_value_pair('sex_label', 'sex'),
  text_equals('Cinsi/Sex', taper=3)('sex_label')
)

aze = combine(
  sn, fn, doe, dob, doi, sex, pob
).with_name('AZE')


# Run on CLI
# ----------

config = Config(num_samples=100)

if __name__ == '__main__':
  bp_cli_main(aze, config=config)