import React from 'react';

import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';

import runBPModel from 'studio/async/runBPModel';

import * as DocRun from 'studio/state/docRun';
import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

type StartedDocRunUUID = UUID;
type State = {
  startedDocRuns: Set<StartedDocRunUUID>;
  numActiveDocRuns: number;
}

export default function useModelRunner(
  project: Project.t | undefined,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext,
) {
  const stateRef = React.useRef<State>({
    startedDocRuns: new Set(),
    numActiveDocRuns: 0,
  });
  const state = stateRef.current;

  React.useEffect(() => {
    if (project != undefined && state != undefined) {
      for (let modelRun of project.modelRuns) {
        if (state.numActiveDocRuns >= project.settings.numSimultaneousModelRuns) {
          break;
        }

        for (let docRun of ModelRun.pendingDocRuns(modelRun)) {
          if (state.numActiveDocRuns >= project.settings.numSimultaneousModelRuns) {
            break;
          }

          if (!state.startedDocRuns.has(docRun.uuid)) {
            state.numActiveDocRuns++;
            start(modelRun, docRun, project,
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
  docRun: DocRun.PendingDocRun,
  project: Project.t,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext,
  state: State)
{
  console.info('Starting model doc run', modelRun, docRun);

  if (state.startedDocRuns.has(docRun.uuid)) {
    console.warn(
      'Attempted to start doc run multiple times; ignoring',
      docRun, project, sessionContext, actionContext, state);
    return;
  }

  state.startedDocRuns.add(docRun.uuid);

  const docName = docRun.docName;
  const modelIndex = modelRun.modelIndex;
  const model = project.modelStack[modelIndex];
  assert(model != undefined);

  try {
    console.info('Running model', docName);

    actionContext.dispatchAction({
      type: 'UpdateModelDocRun',
      modelIndex,
      docRun: {
        type: 'ActiveDocRun',
        uuid: docRun.uuid,
        docName: docRun.docName,
      },
    });

    const results = await runBPModel(
      project.samplesPath,
      docName,
      model,
      Project.blueprintSettings(project),
      sessionContext,
    );

    console.info('Done running model', docName);

    actionContext.dispatchAction({
      type: 'UpdateModelDocRun',
      modelIndex,
      docRun: {
        type: 'FinishedDocRun',
        uuid: docRun.uuid,
        docName: docRun.docName,
        results,
      },
    });
  } catch (error) {
    console.error('Error running model', docName, error);

    actionContext.dispatchAction({
      type: 'UpdateModelDocRun',
      modelIndex,
      docRun: {
        type: 'FailedDocRun',
        uuid: docRun.uuid,
        docName: docRun.docName,
        error: error.toString(),
      },
    });
  } finally {
    state.numActiveDocRuns--;
  }
}
