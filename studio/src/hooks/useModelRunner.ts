import React from 'react';

import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';

import runBPModel from 'studio/async/runBPModel';

import * as RecordRun from 'studio/state/recordRun';
import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

type StartedRecordRunUUID = UUID;
type State = {
  startedRecordRuns: Set<StartedRecordRunUUID>;
  numActiveRecordRuns: number;
}

export default function useModelRunner(
  project: Project.t | undefined,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext,
) {
  const stateRef = React.useRef<State>({
    startedRecordRuns: new Set(),
    numActiveRecordRuns: 0,
  });
  const state = stateRef.current;

  React.useEffect(() => {
    if (project != undefined && state != undefined) {
      for (let modelRun of project.modelRuns) {
        if (state.numActiveRecordRuns >= project.settings.numSimultaneousModelRuns) {
          break;
        }

        for (let recordRun of ModelRun.pendingRecordRuns(modelRun)) {
          if (state.numActiveRecordRuns >= project.settings.numSimultaneousModelRuns) {
            break;
          }

          if (!state.startedRecordRuns.has(recordRun.uuid)) {
            state.numActiveRecordRuns++;
            start(modelRun, recordRun, project,
                  sessionContext, actionContext, state);
          }
        }
      }
    }
  },
  [
    state,
    project?.modelRuns,
    sessionContext,
    actionContext,
  ]);
}

async function start(
  modelRun: ModelRun.t,
  recordRun: RecordRun.PendingRecordRun,
  project: Project.t,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext,
  state: State)
{
  console.info('Starting model doc run', modelRun, recordRun);

  if (state.startedRecordRuns.has(recordRun.uuid)) {
    console.warn(
      'Attempted to start doc run multiple times; ignoring',
      recordRun, project, sessionContext, actionContext, state);
    return;
  }

  state.startedRecordRuns.add(recordRun.uuid);

  const recordName = recordRun.recordName;
  const modelIndex = modelRun.modelIndex;
  const model = project.modelStack[modelIndex];
  assert(model != undefined);

  try {
    console.info('Running model', recordName);

    actionContext.dispatchAction({
      type: 'UpdateModelRecordRun',
      modelIndex,
      recordRun: {
        type: 'ActiveRecordRun',
        uuid: recordRun.uuid,
        recordName: recordRun.recordName,
      },
    });

    const results = await runBPModel(
      project.samplesPath,
      recordName,
      model,
      Project.blueprintSettings(project),
      sessionContext,
    );

    console.info('Done running model', recordName);

    actionContext.dispatchAction({
      type: 'UpdateModelRecordRun',
      modelIndex,
      recordRun: {
        type: 'FinishedRecordRun',
        uuid: recordRun.uuid,
        recordName: recordRun.recordName,
        results,
      },
    });
  } catch (error) {
    console.error('Error running model', recordName, error);

    actionContext.dispatchAction({
      type: 'UpdateModelRecordRun',
      modelIndex,
      recordRun: {
        type: 'FailedRecordRun',
        uuid: recordRun.uuid,
        recordName: recordRun.recordName,
        error: error.toString(),
      },
    });
  } finally {
    state.numActiveRecordRuns--;
  }
}
