import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {BlueprintSettings, makeConfig} from 'studio/state/settings';
import {stringify, writeString} from 'studio/util/stringifyForPython';
import {loadRecordBlob} from 'studio/async/loadRecords';

export default async function runBPModel(
  samplesPath: string,
  recordName: string,
  model: Model.t,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext,
): Promise<Results.t>
{
/*
  const record_blob = await loadRecordBlob(
    samplesPath,
    recordName,
  );
  const config = makeConfig(blueprintSettings);
*/
  throw new Error('Not implemented');
}
