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
  handle: Handle.t):
    Promise<Project.t>
{
  const fileHandle = await handle.getFileHandle('project.json');
  const file = await fileHandle.getFile();
  const text = await file.text();
  const project: Project.t = JSON.parse(text);
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
  handle: Handle.t,
  project: Project.t):
    Promise<SaveProjectResult>
{
  return handle.getFileHandle('project.json').then(
    fileHandle => fileHandle.createWritable()
  ).then(
    writableStream => writableStream.write(JSON.stringify(project))
  ).then(
    (): SaveProjectDone => {
      // console.debug('Save project done', handle, project);
      return {
        status: 'SaveProjectDone',
        project,
        timestamp: new Date(),
      };
    }
  ).catch(
    error => {
      console.error('Save project failed', handle, project, error);
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
