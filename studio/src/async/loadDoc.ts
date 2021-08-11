import memo from 'memoizee';
import * as Doc from 'studio/foundation/doc';
import {loadRecordBlob} from 'studio/async/loadRecords';
import * as Project from 'studio/state/project';
import {BlueprintSettings} from 'studio/state/settings';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {stringify, writeString} from 'studio/util/stringifyForPython';

async function rawLoadDoc(
  samplesPath: string,
  recordName: string,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext):
    Promise<Doc.t>
{
  /*
  const record_blob = await loadRecordBlob(
    samplesPath,
    recordName,
  );
  const doc = generate_doc_from_record_blob(record_blob, ${writeString(recordName)});
  */
  throw new Error('Not implemented');
}

const loadDoc = memo(rawLoadDoc, {max: 500});

export default loadDoc;
