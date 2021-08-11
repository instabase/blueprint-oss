import React from 'react';

import ModalContext from 'studio/context/ModalContext';
import ActionContext from 'studio/context/ActionContext';

import AnnotationModeView from 'studio/components/AnnotationModeView';
import ImagePaneLoader from 'studio/components/ImagePane/Loader';
import DocListPane from 'studio/components/DocListPane';
import NodePane from 'studio/components/NodePane/Pane';
import ModelTreePane from 'studio/components/ModelPane/Pane';
import {Column, Row} from 'studio/components/Split';

import useModalContainer from 'studio/hooks/useModalContainer';
import useExtractions, {Extractions} from 'studio/hooks/useExtractions';
import useKeyboardShortcut from 'studio/hooks/useKeyboardShortcut';

import * as Project from 'studio/state/project';

import * as SB from 'studio/util/splitBreakdown';

type Props = {
  project: Project.t;
};

export default function(props: Props) {
  const actionContext = React.useContext(ActionContext);

  const clearSelectionMode = React.useCallback(
    () => {
      actionContext.dispatchAction({
        type: 'SetSelectedField',
        field: undefined,
      });
    },
    [actionContext],
  );
  
  useKeyboardShortcut({key: 'c'}, clearSelectionMode);

  const extractions = useExtractions(props.project);

  if (false /*Project.docs(props.project).size == 0*/) {
    return (
      <div className="CenteredContainer HugePadding" >
        <div
          className="CenteredText"
          style={{
            maxWidth: '600px',
          }}
        >
          No doc samples found.
        </div>
      </div>
    );
  } else if (Project.annotationMode(props.project)) {
    return (
      <AnnotationModeView project={props.project} />
    );
  } else {
    return (
      <Row
        localStorageSuffix={`MainView-R-${props.project.uuid}`}
        defaultBreakdown={SB.Breakdown_1_1}
      >
        <ModelPane
          {...props}
          extractions={extractions}
        />
        <Column
          localStorageSuffix={`MainView-RC-${props.project.uuid}`}
          defaultBreakdown={SB.Breakdown_3_1}
        >
          <ImagePaneLoader
            {...props}
            extraction={extractions.selected?.extraction}
          />
          <DocListPane {...props} />
        </Column>
      </Row>
    );
  }
}

type ModelPaneProps = Props & {
  extractions: Extractions;
};

function ModelPane(props: ModelPaneProps) {
  const higherModalContext = React.useContext(ModalContext);

  const [modal, dispatchModalAction] = useModalContainer();

  const modalContext = React.useMemo(
    () => ({
      dispatchModalAction,
      currentModal: modal,
      higherModalContext,
    }),
    [
      dispatchModalAction,
      modal,
      higherModalContext,
    ],
  );

  React.useEffect(() => {
    dispatchModalAction({
      name: 'AskModalToClose',
      skipWarningIfNoModal: true,
    });
  }, [Project.model(props.project)]);

  return (
    <div
      style={{
        position: 'relative',
        display: 'grid',
        minWidth: '0px',
        minHeight: '0px',
      }}
    >
      <ModalContext.Provider value={modalContext}>
        {props.project.settings.annotationMode &&
          <NodePane {...props} />
        }

        {!props.project.settings.annotationMode &&
          <Column
            localStorageSuffix={`MainView.ModelPane-${props.project.uuid}`}
            defaultBreakdown={SB.Breakdown_1_3}
          >
            <ModelTreePane
              project={props.project}
            />
            <NodePane {...props} />
          </Column>
        }

        {modal}

      </ModalContext.Provider>
    </div>
  );
}
