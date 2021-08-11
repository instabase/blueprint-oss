import JSZip from 'jszip';
import FileSaver from 'file-saver';

import {Value as TheSessionContext} from 'studio/context/SessionContext';

import * as Project from 'studio/state/project';
import * as Settings from 'studio/state/settings';

import {loadResponse, loadRecordBlob} from 'studio/async/loadRecords';
import {loadImageAsBlob} from 'studio/async/loadImage';
import loadDoc from 'studio/async/loadDoc';

export default async function makeDebugBundle(
  project: Project.t,
  sessionContext: TheSessionContext,
): Promise<void>
{
  const bundleName = `StudioDebugData-${new Date().toISOString()}`;

  console.log('Building debug data');

  let zip = new JSZip();

  console.log('Adding load_records response');
  zip.file(
    `${bundleName}/loadRecordsResponse.json`,
    JSON.stringify(
      await loadResponse(project.samplesPath),
    ),
  );

  const recordName = project.selectedRecordName;

  if (recordName) {
    console.log('Adding record blob for selected doc from load_records');
    const recordBlob = await loadRecordBlob(
      project.samplesPath,
      recordName,
    );
    zip.file(
      `${bundleName}/recordBlob_loadRecords_selectedDoc.json`,
      JSON.stringify(recordBlob),
    );

    console.log('Adding images for selected doc');
    for (let [page_number, layout] of Object.entries(recordBlob.layouts)) {
      const imageBlob = await loadImageAsBlob(layout.processed_image_path);
      zip.file(
        `${bundleName}/image_selectedDoc_page_${page_number}.jpg`,
        imageBlob,
      );
    }

    console.log('Adding doc');
    zip.file(
      `${bundleName}/selectedDoc.json`,
      JSON.stringify(
        await (
          recordName && loadDoc(
            project.samplesPath,
            recordName,
            Project.blueprintSettings(project),
            sessionContext,
          )
        ),
      ),
    );
  }

  console.log('Adding model');
  zip.file(
    `${bundleName}/model.json`,
    JSON.stringify(
      Project.model(project),
    ),
  );

  console.log('Adding project');
  zip.file(
    `${bundleName}/project.json`,
    JSON.stringify(
      project,
    ),
  );

  console.log('Adding Blueprint config');
  zip.file(
    `${bundleName}/blueprint_config.json`,
    JSON.stringify(
      Settings.makeConfig(
        Project.blueprintSettings(
          project,
        ),
      ),
    ),
  );

  console.log('Generating zip file');
  const blob = await zip.generateAsync({type: "blob"});

  await FileSaver.saveAs(
    blob,
    `${bundleName}.zip`,
  );

  console.log('Done generating debug data');
}
