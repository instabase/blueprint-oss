import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {BlueprintSettings, makeConfig} from 'studio/state/settings';
import {stringify, writeString} from 'studio/util/stringifyForPython';
import loadDoc from 'studio/async/loadDoc';
import * as Handle from 'studio/state/handle';

export default async function runBPModel(
  handle: Handle.t,
  docName: string,
  model: Model.t,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext,
): Promise<Results.t>
{
  const doc = await loadDoc(handle, docName, blueprintSettings, sessionContext);

  const endpoint = 'run_bp_model';
  console.log(`Hitting ${endpoint}`, docName, doc, model);
  const response = await fetch(`http://localhost:5000/${endpoint}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      'doc': doc,
      'model': model,
    }),
  });
  const responseJSON = await response.json();
  console.log(`Got response from ${endpoint}`, docName, doc, model, responseJSON);
  if ('error' in responseJSON) {
    console.log(`Error from ${endpoint}`, responseJSON);
    throw responseJSON;
  }
  return responseJSON['results'] as Results.t;
}
