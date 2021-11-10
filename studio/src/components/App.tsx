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
import useRecentProjectsList from 'studio/hooks/useRecentProjectsList';

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

  const [projectPath, setProjectPath] =
    useLocalStorageState<string | undefined>(
      'Studio.LastProjectPath-v1',
      undefined,
      isProjectPath);

  const [recentProjectPaths, setRecentProjectPaths] =
    useRecentProjectsList();

  React.useEffect(() => {
    const MAX_RECENT_PROJECTS = 5;
    if (projectPath != undefined) {
      setRecentProjectPaths([
        projectPath,
        ...recentProjectPaths.filter(path => path != projectPath),
      ].slice(0, MAX_RECENT_PROJECTS));
    }
  }, [projectPath]);

  const sessionContext = React.useMemo(() => ({
    uuid: sessionUUID,
    backendURL: BACKEND_URL,
    projectPath,
    setProjectPath,
  }), [
    sessionUUID,
    projectPath,
    setProjectPath,
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
        recentProjectPaths={recentProjectPaths}
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
  recentProjectPaths: string[];
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
          recentProjectPaths={props.recentProjectPaths}
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
              sessionContext.setProjectPath(undefined);
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
  recentProjectPaths: string[];
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
                  'one containing your image samples, and ' +
                  'one containing your OCR files.\n\n' +
                  'The files must be named as follows: ' +
                  'for every image foo.jpg (or foo.png, etc.), ' +
                  'there must be a corresponding OCR file called ' +
                  'foo.jpg.json (or foo.png.json, etc.).\n\n' +
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

    {props.error &&
      <div className="CenteredText DisallowUserSelection">
        Error loading project at<br/>
        {sessionContext.projectPath}:<br />
        {props.error}
      </div>
    }

    {props.recentProjectPaths.length > 0 &&
      <>
        <div className="CenteredText DisallowUserSelection">
          Recent projects
        </div>

        {props.recentProjectPaths.map(
          projectPath => (
            <button
              onClick={
                event => {
                  event.stopPropagation();
                  event.preventDefault();
                  sessionContext.setProjectPath(projectPath);
                }
              }
            >
              {projectPath}
            </button>
          )
        )}
      </>
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

  const imagesDirName = prompt(
    'Type the name of the subdirectory that has your image files.',
    'img')
  if (!imagesDirName) {
    console.log('User did not provide an images dir name, aborting');
    return;
  }
  if (entries.get(imagesDirName)?.kind != 'directory') {
    const error = 'Error: Images directory not found';
    console.log(error);
    alert(error);
    return;
  }
  console.log('Got images dir name', imagesDirName);

  const ocrDirName = prompt(
    'Type the name of the subdirectory that has your OCR files.',
    'ocr')
  if (!ocrDirName) {
    console.log('User did not provide an OCR dir name, aborting');
    return;
  }
  if (entries.get(ocrDirName)?.kind != 'directory') {
    const error = 'Error: OCR directory not found';
    console.log(error);
    alert(error);
    return;
  }
  console.log('Got OCR dir name', ocrDirName);


}
