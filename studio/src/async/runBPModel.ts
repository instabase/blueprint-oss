import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {BlueprintSettings, makeConfig} from 'studio/state/settings';
import {stringify, writeString} from 'studio/util/stringifyForPython';
import {loadDocBlob} from 'studio/async/loadDocs';
import * as Handle from 'studio/state/handle';

export default async function runBPModel(
  handle: Handle.t,
  docName: string,
  model: Model.t,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext,
): Promise<Results.t>
{
/*
  const doc_blob = await loadDocBlob(
    samplesPath,
    docName,
  );
  const config = makeConfig(blueprintSettings);
*/
  throw new Error('Not implemented');
}
