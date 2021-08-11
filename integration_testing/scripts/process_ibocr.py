#!/usr/bin/env python3


import json
import sys


filename = sys.argv[1]
output_dir = sys.argv[2]

with open(filename) as f:
  record_blobs = json.load(f)
  for record_number, record_blob in enumerate(record_blobs):
    out_file_name = output_dir + '/' + filename
    if True: # len(record_blobs) > 1:
      out_file_name = '.'.join(out_file_name.split('.')[:-1])
      out_file_name = out_file_name + '-' + str(record_number) + '.json'
    with open(out_file_name, 'w') as out_f:
      out_f.write(record_blob['refined_phrases'][0]['word'])
