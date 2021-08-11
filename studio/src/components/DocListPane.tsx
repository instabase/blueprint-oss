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

  const recordNamesResource = useResource(
    Project.activeRecordNames(project)
  );

  // Janky, we could show "loading" better than this.
  const recordNames =
    recordNamesResource.status == 'Done' ?
      recordNamesResource.value : [];

  const selectedRecordName = project.selectedRecordName;
  const model = Project.model(project);
  
  return (
    <DocListView project={project} recordNames={recordNames}>
      <div className="CornerButtons _high">
        <button
          disabled={!selectedRecordName}
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              assert(selectedRecordName);
              actionContext.dispatchAction({
                type: 'ScheduleModelRun',
                modelIndex: project.currentModelIndex,
                recordNames: [selectedRecordName],
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
            recordNames,
            pin: true,
          });
        }}>
          <CollectionPlay/>
        </button>
      </div>
    </DocListView>
  );
}
