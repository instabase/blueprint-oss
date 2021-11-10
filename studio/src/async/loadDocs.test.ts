import * as LR from './loadDocs';

import * as ibdoc__map_docs__entire_doc from '../../../integration_testing/load_docs_output/ibdoc__map_docs__entire_doc.json';
import * as ibdoc__map_docs__split_by_page from '../../../integration_testing/load_docs_output/ibdoc__map_docs__split_by_page.json';
import * as ibdoc__process_files from '../../../integration_testing/load_docs_output/ibdoc__process_files.json';
import * as ibocr__map_docs__entire_doc from '../../../integration_testing/load_docs_output/ibocr__map_docs__entire_doc.json';
import * as ibocr__map_docs__split_by_page from '../../../integration_testing/load_docs_output/ibocr__map_docs__split_by_page.json';
import * as ibocr__process_files from '../../../integration_testing/load_docs_output/ibocr__process_files.json';

test('number of docs', () => {
  expect(LR.loadDocNamesFromResponse(ibdoc__map_docs__entire_doc)).toHaveLength(1);
  expect(LR.loadDocNamesFromResponse(ibdoc__map_docs__split_by_page)).toHaveLength(2);
  expect(LR.loadDocNamesFromResponse(ibdoc__process_files)).toHaveLength(2);
  expect(LR.loadDocNamesFromResponse(ibocr__map_docs__entire_doc)).toHaveLength(1);
  expect(LR.loadDocNamesFromResponse(ibocr__map_docs__split_by_page)).toHaveLength(2);
  expect(LR.loadDocNamesFromResponse(ibocr__process_files)).toHaveLength(2);
});
