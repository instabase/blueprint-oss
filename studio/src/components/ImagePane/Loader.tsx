import React from 'react';

import * as Extraction from 'studio/foundation/extraction';

import Pane from './Pane';

import SessionContext from 'studio/context/SessionContext';

import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';
import * as Handle from 'studio/state/handle';

import useResource from 'studio/hooks/useResource';

import {loadLayouts} from 'studio/async/loadDocs';
import loadImage from 'studio/async/loadImage';
import loadDoc from 'studio/async/loadDoc';

import assert from 'studio/util/assert';

type Props = {
  project: Project.t;
  extraction: Extraction.t | undefined;
};

export default function Loader(props: Props) {
  const sessionContext = React.useContext(SessionContext);

  const docName = props.project.selectedDocName;

  const layoutsPromise = docName
    ? loadLayouts(
        sessionContext.handle as Handle.t,
        docName,
      )
    : undefined;
  const layoutsResource = useResource(layoutsPromise);

  const docPromise = docName
    ? loadDoc(
        sessionContext.handle as Handle.t,
        docName,
        Project.blueprintSettings(props.project),
        sessionContext,
      )
    : undefined;
  const docResource = useResource(docPromise);

  if (!docName) {
    return <CenteredText>Select a document</CenteredText>;
  } else if (layoutsResource.status == 'NotAvailable')
  {
    return <CenteredText>No image available for selected doc</CenteredText>;
  } else if (docResource == undefined ||
             docResource.status == 'NotAvailable') {
    return <CenteredText>No entities available for selected doc</CenteredText>;
  }

  const resources = [
    layoutsResource,
    docResource,
  ];

  switch (Resource.worstStatus(resources.map(res => res.status))) {
    case 'NotAvailable':
      assert(false);
      return (
        <CenteredText>
          Error: some resource is not available
        </CenteredText>
      );
    case 'NotLoaded':
    case 'Loading':
      return (
        <CenteredText>
          Loading...
        </CenteredText>
      );
    case 'Done':
      assert(Resource.isDone(layoutsResource));
      assert(Resource.isDone(docResource));
      return (
        <Pane
          project={props.project}
          extraction={props.extraction}
          docName={docName}
          doc={Resource.finished(docResource)}
          layouts={layoutsResource.value}
        />
      );
    case 'Failed':
      return (
        <CenteredText>
          {Resource.isFailed(layoutsResource) && layoutsResource.errorMessage}<br />
          {Resource.isFailed(docResource) && docResource.errorMessage}<br />
        </CenteredText>
      );
  }
}

function CenteredText(props: {children: any}) {
  return <div className="CenteredContainer HugePadding">
    <div className="CenteredText">
      {props.children}
    </div>
  </div>;
}
