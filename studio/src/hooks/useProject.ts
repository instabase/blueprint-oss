import React from 'react';

import * as Targets from 'studio/foundation/targets';

import * as Model from 'studio/blueprint/model';

import {Value as TheSessionContext} from 'studio/context/SessionContext';

import * as AutosaverState from 'studio/state/autosaverState';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';
import mainReducer, {Action} from 'studio/state/mainReducer';

import useTriggerUpdate from 'studio/hooks/useTriggerUpdate';

import {SaveProjectResult, loadProject, saveProject} from 'studio/async/project';

import useResource from 'studio/hooks/useResource';

import assert from 'studio/util/assert';

function useInitialProject(sessionContext: TheSessionContext): Resource.t<Project.t> {
  const getter = React.useMemo(() => {
    const path = sessionContext.projectPath;
    if (path == undefined) {
      return undefined;
    } else {
      return loadProject(sessionContext, path);
    }
  }, [sessionContext]);

  return useResource(getter);
}

function initialAutosaverState(
  sessionContext: TheSessionContext):
    AutosaverState.t
{
  return {
    sessionContext,
    enqueued: undefined,
    projectBeingSaved: undefined,
    lastSaveResult: undefined,
  };
}

function useAutosaveProject(sessionContext: TheSessionContext) {
  const triggerUpdate = useTriggerUpdate();

  const totallyDeadRef =
    React.useRef<boolean>(false);

  const stateRef =
    React.useRef<AutosaverState.t>(
      initialAutosaverState(
        sessionContext));

  React.useEffect(() => {
    const doConfirm = (event: BeforeUnloadEvent) => {
      if (!totallyDeadRef.current) {
        if (stateRef.current.enqueued) {
          const confirmationString = 'Unsaved changes -- exit anyway?';
          event.preventDefault();
          event.returnValue = confirmationString;
          return confirmationString;
        }
      }
    };

    const doDie = (event: Event) => {
      totallyDeadRef.current = true;
    };

    window.addEventListener('beforeunload', doConfirm);
    window.addEventListener('pagehide', doDie);

    return () => {
      window.removeEventListener('beforeunload', doConfirm);
      window.removeEventListener('pagehide', doDie);
    };
  }, []);

  if (sessionContext != stateRef.current.sessionContext) {
    stateRef.current = 
      initialAutosaverState(
        sessionContext);
  }

  const state = stateRef.current;

  const scheduleAutosave = React.useCallback(
    (project: Project.t): void => {
      const shouldSave = () => (
        state.projectBeingSaved == undefined &&
        state.enqueued != undefined &&
        !totallyDeadRef.current
      );

      const startSaving = () => {
        assert(state.projectBeingSaved == undefined);
        assert(state.enqueued != undefined);
        state.projectBeingSaved = state.enqueued;
        state.enqueued = undefined;
        triggerUpdate();

        saveProject(
          state.sessionContext,
          state.projectBeingSaved,
          state.sessionContext.projectPath as string,
        ).then(
          (result: SaveProjectResult) => {
            assert(state.projectBeingSaved == result.project);
            state.projectBeingSaved = undefined;
            state.lastSaveResult = result;
            triggerUpdate();

            setTimeout(() => {
              if (shouldSave()) {
                startSaving();
              }
            }, 1000);
          }
        );
      };

      const notCurrentlySavingAProject =
        state.projectBeingSaved == undefined;

      const thisIsTheMostRecentlySavedProject =
        state.lastSaveResult?.project == project;

      const savingAnotherProject =
        state.projectBeingSaved != undefined &&
        state.projectBeingSaved != project;
      
      if (savingAnotherProject ||
          (notCurrentlySavingAProject &&
           !thisIsTheMostRecentlySavedProject))
      {
        state.enqueued = project;
        // triggerUpdate();
      }

      setTimeout(() => {
        if (shouldSave()) {
          startSaving();
        }
      }, 1000);
    }, [state]
  );

  return {
    scheduleAutosave,
    autosaverState: state,
  };
}

type Result = {
  projectResource: Resource.t<Project.t>;
  dispatchAction: (action: Action) => void;
  autosaverState: AutosaverState.t;
};

export default function useProject(
  sessionContext: TheSessionContext):
    Result
{
  const triggerUpdate = useTriggerUpdate();

  const initialProject =
    useInitialProject(sessionContext);

  const projectRef =
    React.useRef<Project.t | undefined>();

  const resetProjectRef = () => {
    projectRef.current = undefined;
  };

  const previousSessionContextRef =
    React.useRef<TheSessionContext | undefined>();

  if (sessionContext != previousSessionContextRef.current) {
    resetProjectRef();
  }

  previousSessionContextRef.current = sessionContext;

  const tryToPopulateProjectRef = () => {
    if (initialProject.status == 'Done') {
      projectRef.current = initialProject.value;
    }
  };

  if (projectRef.current == undefined) {
    tryToPopulateProjectRef();
  }

  const {scheduleAutosave, autosaverState} =
    useAutosaveProject(sessionContext);

  if (projectRef.current != undefined &&
      initialProject.status == 'Done' &&
      projectRef.current != initialProject.value)
  {
    scheduleAutosave(projectRef.current);
  }

  const dispatchAction = React.useCallback(
    (action: Action) => {
      if (projectRef.current != undefined) {
        projectRef.current =
          mainReducer(
            projectRef.current,
            action);
        triggerUpdate();
      } else {
        console.warn('Attempted to dispatch an action before ' +
                     'project was loaded; ignoring');
      }
    }, [sessionContext]
  );

  const projectResource: Resource.t<Project.t> =
    projectRef.current != undefined
      ? {status: 'Done', value: projectRef.current}
      : initialProject;

  return {
    projectResource,
    dispatchAction,
    autosaverState,
  };
}
