import React from 'react';
import DocListView from 'studio/components/DocListView';
import useResource from 'studio/hooks/useResource';
import * as Project from 'studio/state/project';

type Props = {
  project: Project.t;
};

export default function DocListPane({project}: Props) {
  const recordNamesResource = useResource(
    Project.activeRecordNames(project)
  );

  // Janky, we could show "loading" better than this.
  const recordNames =
    recordNamesResource.status == 'Done' ?
      recordNamesResource.value : [];

  return (
    <DocListView
      project={project}
      recordNames={recordNames}
    />
  );
}
