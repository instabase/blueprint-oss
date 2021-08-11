import json

from unittest import TestCase

from bp import (
  generate_doc_from_record_blob,
)


class TestUDFLoadRecordBlob(TestCase):

  def test_all_samples(self) -> None:
    paths = [
      '../integration_testing/udf_load_record_blob_output/ibdoc__map_records__entire_doc__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibdoc__map_records__split_by_page__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibdoc__map_records__split_by_page__doc_1-1.json',
      '../integration_testing/udf_load_record_blob_output/ibdoc__process_files__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibdoc__process_files__doc_1-1.json',
      '../integration_testing/udf_load_record_blob_output/ibocr__map_records__entire_doc__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibocr__map_records__split_by_page__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibocr__map_records__split_by_page__doc_1-1.json',
      '../integration_testing/udf_load_record_blob_output/ibocr__process_files__doc_1-0.json',
      '../integration_testing/udf_load_record_blob_output/ibocr__process_files__doc_1-1.json',
    ]

    for path in paths:
      with open(path) as f:
        generate_doc_from_record_blob(json.load(f), 'fake_record_name')
