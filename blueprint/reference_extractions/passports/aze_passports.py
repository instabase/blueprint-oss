#!/usr/bin/env python3

from bp import *

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
