import {Value as TheSessionContext} from 'studio/context/SessionContext';
import * as Project from 'studio/state/project';
import * as Settings from 'studio/state/settings';
import * as debug from 'studio/util/debug';

export type SaveProjectDone = {
  status: 'SaveProjectDone';
  timestamp: Date;
  project: Project.t;
};

export type SaveProjectFailed = {
  status: 'SaveProjectFailed';
  timestamp: Date;
  project: Project.t;
  errorCode: number;
  errorMessage: string;
};

export type SaveProjectResult =
  | SaveProjectDone
  | SaveProjectFailed
;

export async function loadProject(
  sessionContext: TheSessionContext,
  projectPath: string):
    Promise<Project.t>
{
  const response = await fetch(
    sessionContext.backendURL + '/read_file' + projectPath);
  const project: Project.t = await response.json();
  return validate(project);
}

function validate(project: Project.t): Project.t {
  // FIXME: Schema validations.

  if (project.formatVersion != Project.FORMAT_VERSION) {
    throw 'Unsupported version of project file format';
  }

  if (project.selectionMode == undefined) {
    project = {...project, selectionMode: {type: 'None'}};
  }

  return {
    ...project,
    settings: Settings.fill(project.settings),
    targets: {
      ...project.targets,
      schema:
        Project.syncSchemaTypes(
          Project.model(project),
          project.targets.schema),
    },
  };
}

export async function saveProject(
  sessionContext: TheSessionContext,
  project: Project.t,
  projectPath: string):
    Promise<SaveProjectResult>
{
  return fetch(sessionContext.backendURL + '/write_file' + projectPath, {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  }).then(
    (): SaveProjectDone => {
      // console.debug('Save project done', sessionContext, project, projectPath);
      return {
        status: 'SaveProjectDone',
        project,
        timestamp: new Date(),
      };
    }
  ).catch(
    error => {
      console.error('Save project failed', sessionContext, project, projectPath, error);
      return { // Kinda janky that we resolve rather than reject here.
        status: 'SaveProjectFailed',
        project,
        timestamp: new Date(),
        errorCode: -1,
        errorMessage: error ? error.toString() : 'Unknown error',
      };
    }
  );
}
