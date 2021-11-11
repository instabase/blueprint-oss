import memo from 'memoizee';
import * as Doc from 'studio/foundation/doc';
import {loadDocBlob} from 'studio/async/loadDocs';
import * as Project from 'studio/state/project';
import {BlueprintSettings} from 'studio/state/settings';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {stringify, writeString} from 'studio/util/stringifyForPython';
import * as Handle from 'studio/state/handle';

async function rawLoadDoc(
  handle: Handle.t,
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
  return {
    bbox: {
      ix: {
        a: 0,
        b: 0,
      },
      iy: {
        a: 0,
        b: 0,
      },
    },
    entities: [],
    name: docName,
  };
}

const loadDoc = memo(rawLoadDoc, {max: 500});

export default loadDoc;
