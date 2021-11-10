import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import * as Project from 'studio/state/project';

import loadDoc from 'studio/async/loadDoc';
import loadImage from 'studio/async/loadImage';
import {loadLayouts} from 'studio/async/loadDocs';

export function preloadResourcesForSelectedDocName(
  project: Project.t,
  sessionContext: TheSessionContext)
{
  const docName = project.selectedDocName;
  if (docName != undefined) {
    preloadResourcesForDoc(
      project,
      docName,
      sessionContext,
    );
  }
}

export async function preloadResourcesForDoc(
  project: Project.t,
  docName: string,
  sessionContext: TheSessionContext)
{
  try {
    await loadDoc(
      project.samplesPath,
      docName,
      Project.blueprintSettings(project),
      sessionContext,
    );

    const layouts = Object.values(
      await loadLayouts(
        project.samplesPath,
        docName,
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
      project, docName, e,
    );
  }
}
