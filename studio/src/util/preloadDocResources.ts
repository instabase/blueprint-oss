import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import * as Project from 'studio/state/project';

import loadDoc from 'studio/async/loadDoc';
import loadImage from 'studio/async/loadImage';
import {loadLayouts} from 'studio/async/loadRecords';

export function preloadResourcesForSelectedRecordName(
  project: Project.t,
  sessionContext: TheSessionContext)
{
  const recordName = project.selectedRecordName;
  if (recordName != undefined) {
    preloadResourcesForRecord(
      project,
      recordName,
      sessionContext,
    );
  }
}

export async function preloadResourcesForRecord(
  project: Project.t,
  recordName: string,
  sessionContext: TheSessionContext)
{
  try {
    await loadDoc(
      project.samplesPath,
      recordName,
      Project.blueprintSettings(project),
      sessionContext,
    );

    const layouts = Object.values(
      await loadLayouts(
        project.samplesPath,
        recordName,
      )
    );

    await Promise.all(
      layouts.map(
        layout => (
          loadImage(layout.processed_image_path)
        )
      )
    );
  } catch (e) {
    console.error(
      'Preloading resources failed',
      project, recordName, e,
    );
  }
}
