import React from 'react';

import * as Extraction from 'studio/foundation/extraction';
import * as Doc from 'studio/foundation/doc';
import * as Targets from 'studio/foundation/targets';

import ActionContext, {Value as TheActionContext} from 'studio/context/ActionContext';

import ProgressStack from 'studio/components/ProgressStack';
import {Props as CheckboxProps} from 'studio/components/Checkbox';

import EntityTypePicker from 'studio/components/ImagePane/EntityTypePicker';
import TargetPicker from 'studio/components/ImagePane/TargetPicker';
import Backdrop from 'studio/components/ImagePane/Backdrop';
import ImageStack from 'studio/components/ImagePane/ImageStack';
import DocEntitiesOverlay from 'studio/components/ImagePane/DocEntitiesOverlay';
import TargetValuesOverlay from 'studio/components/ImagePane/TargetValuesOverlay';
import ExtractedValuesOverlay from 'studio/components/ImagePane/ExtractedValuesOverlay';

import * as ModelRun from 'studio/state/modelRun';
import * as NodeRecordTargets from 'studio/state/nodeRecordTargets';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';

import useOptions, {Values} from 'studio/hooks/useOptions';
import useLocalStorageState from 'studio/hooks/useLocalStorageState';
import useZoomAndPanTransform from 'studio/hooks/useZoomAndPanTransform';

import {isBoolean} from 'studio/util/types';

import {Layouts} from 'studio/async/loadRecords';

import './Pane.css';

type Props = {
  project: Project.t;
  recordName: string;
  doc: Doc.t | undefined;
  layouts: Layouts;
  extraction: Extraction.t | undefined;
};

export default function Pane(props: Props) {
  const actionContext = React.useContext(ActionContext);

  const [transform, setTransform] =
    useZoomAndPanTransform(
      props.project.uuid + props.recordName);

  const targets =
    Project.recordTargets(
      props.project,
      props.recordName);

  const defaultEntityTypeOptions =
    React.useMemo(() => {
      if (props.doc == undefined) {
        return {};
      } else {
        const typeNames =
          Doc.typeNames(
            props.doc);
        const result: Values = {};
        typeNames.forEach(
          typeName => result[typeName] = true);
        return result;
      }
    }, [props.doc]);

  const entityTypeOptions =
    useOptions(
      'ImagePane_EntityTypePicker',
      defaultEntityTypeOptions);

  // The "Targets" checkbox.
  const [targetValuesChecked, setTargetValuesChecked] =
    useLocalStorageState(
      'Studio.ImagePane.ShowTargetValues-v1',
      true,
      isBoolean);

  const [extractedValuesChecked, setExtractedValuesChecked] =
    useLocalStorageState(
      'Studio.ImagePane.ShowExtractedValues-v1',
      true,
      isBoolean);

  return (
    <div className="ImagePane_Pane">
      <Backdrop
        transform={transform}
        setTransform={setTransform}
      >
        <TargetPicker
          project={props.project}
          recordName={props.recordName}
          doc={props.doc}
        >
          <ImageStack
            layouts={props.layouts}
            transform={transform}
          >
            {props.doc &&
              <DocEntitiesOverlay
                project={props.project}
                recordName={props.recordName}
                doc={props.doc}
                entityTypeOptions={entityTypeOptions}
              />
            }

            {targets &&
              <TargetValuesOverlay
                project={props.project}
                recordName={props.recordName}
                targets={targets}
                targetValuesChecked={targetValuesChecked}
              />
            }

            {props.doc && props.extraction &&
              <ExtractedValuesOverlay
                project={props.project}
                doc={props.doc}
                extraction={props.extraction}
                extractedValuesChecked={extractedValuesChecked}
              />
            }
          </ImageStack>
        </TargetPicker>
      </Backdrop>

      <EntityTypePicker
        selectionMode={props.project.selectionMode}
        entityTypeOptions={entityTypeOptions}
        targetValuesOption={{
          checked: targets != undefined &&
                   targetValuesChecked,
          disabled: targets == undefined,
          setChecked: setTargetValuesChecked,
        }}
        extractedValuesOption={{
          checked: props.extraction != undefined &&
                   extractedValuesChecked,
          disabled: props.extraction == undefined,
          setChecked: setExtractedValuesChecked,
        }}
      />

      <ProgressStack
        widgetProps={progressWidgetProps(props.project, actionContext)}
      />
    </div>
  );
}

function progressWidgetProps(
  project: Project.t,
  actionContext: TheActionContext)
{
  return ModelRun.pendingModelRuns(project.modelRuns).map(
    modelRun => ({
      taskUUID: modelRun.uuid,
      numerator: ModelRun.numFinalizedRecordRuns(modelRun),
      denominator: ModelRun.numRecordRuns(modelRun),
      onCancel: () => {
        actionContext.dispatchAction({
          type: 'CancelModelRun',
          uuid: modelRun.uuid,
        });
      },
    })
  );
}
