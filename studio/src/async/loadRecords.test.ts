import * as LR from './loadRecords';

import * as ibdoc__map_records__entire_doc from '../../../integration_testing/load_records_output/ibdoc__map_records__entire_doc.json';
import * as ibdoc__map_records__split_by_page from '../../../integration_testing/load_records_output/ibdoc__map_records__split_by_page.json';
import * as ibdoc__process_files from '../../../integration_testing/load_records_output/ibdoc__process_files.json';
import * as ibocr__map_records__entire_doc from '../../../integration_testing/load_records_output/ibocr__map_records__entire_doc.json';
import * as ibocr__map_records__split_by_page from '../../../integration_testing/load_records_output/ibocr__map_records__split_by_page.json';
import * as ibocr__process_files from '../../../integration_testing/load_records_output/ibocr__process_files.json';

test('number of records', () => {
  expect(LR.loadRecordNamesFromResponse(ibdoc__map_records__entire_doc)).toHaveLength(1);
  expect(LR.loadRecordNamesFromResponse(ibdoc__map_records__split_by_page)).toHaveLength(2);
  expect(LR.loadRecordNamesFromResponse(ibdoc__process_files)).toHaveLength(2);
  expect(LR.loadRecordNamesFromResponse(ibocr__map_records__entire_doc)).toHaveLength(1);
  expect(LR.loadRecordNamesFromResponse(ibocr__map_records__split_by_page)).toHaveLength(2);
  expect(LR.loadRecordNamesFromResponse(ibocr__process_files)).toHaveLength(2);
});
