import React from 'react';
import {ErrorBoundary} from 'react-error-boundary';

import ModalContext from 'studio/context/ModalContext';
import SessionContext, {Value as TheSessionContext} from 'studio/context/SessionContext';
import ActionContext from 'studio/context/ActionContext';
import ProjectContext from 'studio/context/ProjectContext';

import StatusBar from 'studio/components/StatusBar';
import MainView from 'studio/components/MainView';
import MenuBar from 'studio/components/MenuBar';

import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';
import * as Handle from 'studio/state/handle';
import mainReducer from 'studio/state/mainReducer';

import useProject from 'studio/hooks/useProject';
import useModalContainer from 'studio/hooks/useModalContainer';
import useIntegerColors from 'studio/hooks/useIntegerColors';
import useLocalStorageState from 'studio/hooks/useLocalStorageState';
import useModelRunner from 'studio/hooks/useModelRunner';

import {saveProject} from 'studio/async/project';
import {UUID, isString} from 'studio/util/types';
import {v4 as uuidv4} from 'uuid';

import 'studio/components/CornerButtons.css';
import 'studio/components/HiddenButtons.css';

const BACKEND_URL = 'http://localhost:5000';

export default function App() {

  // Stateless random init crap
  // ==========================

  useIntegerColors();

  // Stateful stuff
  // ==============

  // App context
  // -----------

  const [modal, dispatchModalAction] = useModalContainer();
  const modalContext = React.useMemo(
    () => ({dispatchModalAction, currentModal: modal}),
    [dispatchModalAction, modal]);

  // Session context
  // ---------------

  const [sessionUUID] = React.useState<UUID>(uuidv4());

  const [handle, setHandle] = React.useState<Handle.t | undefined>(undefined);

  const sessionContext = React.useMemo(() => ({
    uuid: sessionUUID,
    backendURL: BACKEND_URL,
    handle,
    setHandle,
  }), [
    sessionUUID,
    handle,
    setHandle,
  ]);

  // Project context
  // ---------------

  const {projectResource, dispatchAction, autosaverState} =
    useProject(sessionContext);

  const project = Resource.finished(projectResource);

  const projectContext = React.useMemo(
    () => ({project: Resource.finished(projectResource)}),
    [projectResource]);

  // Action context
  // --------------

  const actionContext = React.useMemo(
    () => ({dispatchAction}),
    [dispatchAction],
  );

  useModelRunner(
    project,
    sessionContext,
    actionContext,
  );

  // Menu bar
  // ========

  return (
    <ModalContext.Provider value={modalContext}>
    <SessionContext.Provider value={sessionContext}>
    <ProjectContext.Provider value={projectContext}>
    <ActionContext.Provider value={actionContext}>
      <MenuBar
        project={project}
        haveModal={modal != undefined}
        modalContext={modalContext}
        sessionContext={sessionContext}
        actionContext={actionContext}
      />
      <MainViewLoader
        projectResource={projectResource}
      />
      <StatusBar
        autosaverState={autosaverState}
      />
      {modal}
    </ActionContext.Provider>
    </ProjectContext.Provider>
    </SessionContext.Provider>
    </ModalContext.Provider>
  );
}

type MainViewLoaderProps = {
  projectResource: Resource.t<Project.t>;
};

function MainViewLoader(props: MainViewLoaderProps) {
  const sessionContext = React.useContext(SessionContext);

  switch (props.projectResource.status) {
    case 'NotLoaded':
    case 'NotAvailable':
    case 'Failed':
      return (
        <NoProjectLoadedView
          error={
            props.projectResource.status == 'Failed'
              ? props.projectResource.errorMessage
              : undefined
          }
        />
      );
    case 'Loading':
      return (
        <div className="CenteredContainer">
          <div className="CenteredText DisallowUserSelection">
            Loading...
          </div>
        </div>
      );
    case 'Done':
      const project = props.projectResource.value;
      return (
        <ErrorBoundary
          FallbackComponent={FatalErrorView}
          onReset={
            () => {
              console.error('Fatal error, resetting open project');
              sessionContext.setHandle(undefined);
            }
          }
        >
          <MainView project={project} />
        </ErrorBoundary>
      );
  }
}

type FatalErrorViewProps = {
  error: any;
  resetErrorBoundary: () => void;
};

function FatalErrorView({error, resetErrorBoundary}: FatalErrorViewProps) {
  return (
    <div className="SimpleVerticalStack">
      <div className="CenteredText">
        Fatal error!
      </div>

      <div className="CenteredText">
        Please take a screenshot of your console in Chrome dev tools,
        and report this. Thanks!
      </div>

      <div className="CenteredText">
        {error.message}
      </div>

      <button onClick={resetErrorBoundary}>
        Reset
      </button>
    </div>
  );
}

function isProjectPath(o: unknown): o is string | undefined {
  return isString(o) || o == undefined;
}

type NoProjectLoadedViewProps = {
  error: string | undefined;
};

function NoProjectLoadedView(props: NoProjectLoadedViewProps) {
  const modalContext = React.useContext(ModalContext);
  const sessionContext = React.useContext(SessionContext);

  return <div className="SimpleVerticalStack">
    <div className="CenteredText DisallowUserSelection">
      Welcome to Studio
    </div>

    <div className="SimpleHorizontalStack">
      <button
        onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            console.log('Beginning create new project interaction');

            alert('Select your project\'s root folder. ' +
                  'This folder should already have in it two subdirectories: ' +
                  'one called images/ containing your image samples, and ' +
                  'one called ocr/ containing your OCR files.\n\n' +
                  'The files in these folders must be named as follows: ' +
                  'for every image images/foo.jpg (or images/foo.png, etc.), ' +
                  'there must be a corresponding OCR file called ' +
                  'ocr/foo.jpg.json (or ocr/foo.png.json, etc.).\n\n' +
                  'Your project file will be called project.json. ' +
                  'It is not possible to pick another name. ' +
                  'As a consequence, you cannot have multiple projects ' +
                  'working with the same image/OCR samples. ' +
                  'To do so, make a copy of your sample data.');
            // @ts-ignore
            window.showDirectoryPicker().then(
              (handle: any) => runNewProjectModalInteraction(
                handle as (Handle.t | undefined), sessionContext));
          }
        }
      >
        New project...
      </button>
    </div>

    <div className="SimpleHorizontalStack">
      <button
        onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();

            console.log('Beginning load project interaction');

            // @ts-ignore
            window.showDirectoryPicker().then(
              (handle: Handle.t | undefined) => {
                if (!handle) {
                  console.log('User did not select a project foler, aborting');
                  return;
                }

                handle.getFileHandle('project.json').then(
                  fileHandle => {
                    console.log('Found project.json, loading project');
                    sessionContext.setHandle(handle);
                  }
                ).catch(
                  error => {
                    console.log('Error looking for project.json', error);
                    alert('Error: could not find project.json.\n\n' +
                          'Please select a folder which contains a ' +
                          'project.json file, or click "New project..."');
                  }
                );
              }
            );
          }
        }
      >
        Open project folder...
      </button>
    </div>

    {props.error &&
      <div className="CenteredText DisallowUserSelection">
        Error loading project<br/>
        {props.error}
      </div>
    }
  </div>;
}

async function runNewProjectModalInteraction(
    handle: Handle.t | undefined,
    sessionContext: TheSessionContext)
{
  // @ts-ignore
  if (!handle) {
    console.log('No dir handle, returning');
    return;
  }
  console.log('Got directory from user', handle.entries());

  const entries = new Map<any, any>();
  for await (let [k, v] of handle.entries()) {
    entries.set(k, v);
  }
  console.log('Got contents of directory', entries);

  const projectFileName = 'project.json';
  if (entries.has(projectFileName)) {
    const error = 'Error: Chosen directory already has a project.json file';
    console.log(error);
    alert(error);
    return;
  }

  const imagesDirName = 'images';
  if (entries.get(imagesDirName)?.kind != 'directory') {
    const error = 'Error: Images directory not found';
    console.log(error);
    alert(error);
    return;
  }
  console.log('Got images dir name', imagesDirName);

  const ocrDirName = 'ocr';
  if (entries.get(ocrDirName)?.kind != 'directory') {
    const error = 'Error: OCR directory not found';
    console.log(error);
    alert(error);
    return;
  }
  console.log('Got OCR dir name', ocrDirName);

  await handle.getFileHandle('project.json', {create: true});
  await saveProject(handle, Project.build());

  console.log('Done building new project, setting session handle...');

  sessionContext.setHandle(handle);
}
