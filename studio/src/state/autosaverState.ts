import {Value as TheSessionContext} from 'studio/context/SessionContext';
import * as Project from 'studio/state/project';
import {SaveProjectResult} from 'studio/async/project';

export type t = {
  sessionContext: TheSessionContext;
  enqueued: Project.t | undefined;
  projectBeingSaved: Project.t | undefined;
  lastSaveResult: SaveProjectResult | undefined;
};
