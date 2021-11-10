import React from 'react';
import ActionContext from 'studio/context/ActionContext';
import DocListView from 'studio/components/DocListView';
import {CollectionPlay, PlayBtn} from 'studio/components/StockSVGs';
import useResource from 'studio/hooks/useResource';
import * as Project from 'studio/state/project';
import assert from 'studio/util/assert';

type Props = {
  project: Project.t;
};

export default function DocListPane({project}: Props) {
  const actionContext = React.useContext(ActionContext);

  const docNamesResource = useResource(
    Project.activeDocNames(project)
  );

  // Janky, we could show "loading" better than this.
  const docNames =
    docNamesResource.status == 'Done' ?
      docNamesResource.value : [];

  const selectedDocName = project.selectedDocName;
  const model = Project.model(project);
  
  return (
    <DocListView project={project} docNames={docNames}>
      <div className="CornerButtons _high">
        <button
          disabled={!selectedDocName}
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              assert(selectedDocName);
              actionContext.dispatchAction({
                type: 'ScheduleModelRun',
                modelIndex: project.currentModelIndex,
                docNames: [selectedDocName],
                pin: false,
              });
            }
          }
        >
          <PlayBtn/>
        </button>
        <button onClick={event => {
          event.stopPropagation();
          event.preventDefault();
          actionContext.dispatchAction({
            type: 'ScheduleModelRun',
            modelIndex: project.currentModelIndex,
            docNames,
            pin: true,
          });
        }}>
          <CollectionPlay/>
        </button>
      </div>
    </DocListView>
  );
}
