import React from 'react';
import SessionContext from 'studio/context/SessionContext';
import DocListView from 'studio/components/DocListView';
import useResource from 'studio/hooks/useResource';
import * as Handle from 'studio/state/handle';
import * as Project from 'studio/state/project';

type Props = {
  project: Project.t;
};

export default function DocListPane({project}: Props) {
  const sessionContext = React.useContext(SessionContext);

  const docNamesResource = useResource(
    Project.activeDocNames(
      sessionContext.handle as Handle.t,
      project));

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
