import memo from 'memoizee';
import * as Doc from 'studio/foundation/doc';
import {loadDocBlob} from 'studio/async/loadDocs';
import * as Project from 'studio/state/project';
import {BlueprintSettings} from 'studio/state/settings';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {stringify, writeString} from 'studio/util/stringifyForPython';

async function rawLoadDoc(
  samplesPath: string,
  docName: string,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext):
    Promise<Doc.t>
{
  /*
  const doc_blob = await loadDocBlob(
    samplesPath,
    docName,
  );
  const doc = generate_doc_from_doc_blob(doc_blob, ${writeString(docName)});
  */
  throw new Error('Not implemented');
}

const loadDoc = memo(rawLoadDoc, {max: 500});

export default loadDoc;
