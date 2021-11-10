import React from 'react';
import DocListView from 'studio/components/DocListView';
import useResource from 'studio/hooks/useResource';
import * as Project from 'studio/state/project';

type Props = {
  project: Project.t;
};

export default function DocListPane({project}: Props) {
  const docNamesResource = useResource(
    Project.activeDocNames(project)
  );

  // Janky, we could show "loading" better than this.
  const docNames =
    docNamesResource.status == 'Done' ?
      docNamesResource.value : [];

  return (
    <DocListView
      project={project}
      docNames={docNames}
    />
  );
}
