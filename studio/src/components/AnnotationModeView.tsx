import React from 'react';

import ModalContext from 'studio/context/ModalContext';

import AnnotationDocListPane from 'studio/components/AnnotationDocListPane';
import AnnotateFieldsTable from 'studio/components/AnnotateFieldsTable';
import ImagePaneLoader from 'studio/components/ImagePane/Loader';
import {Column, Row} from 'studio/components/Split';

import * as Project from 'studio/state/project';

import * as SB from 'studio/util/splitBreakdown';

type Props = {
  project: Project.t;
};

export default function(props: Props) {
  return (
    <Row
      localStorageSuffix={`AnnotationModeView-R-${props.project.uuid}`}
      defaultBreakdown={SB.Breakdown_1_2}
    >
      <Column
        localStorageSuffix={`AnnotationModeView-RC-${props.project.uuid}`}
        defaultBreakdown={SB.Breakdown_1_1}
      >
        <AnnotateFieldsTable
          {...props}
        />
        <AnnotationDocListPane {...props} />
      </Column>
      <ImagePaneLoader
        {...props}
        extraction={undefined}
      />
    </Row>
  );
}
