import React from 'react';
import DragSelectionArea from 'studio/components/DragSelectionArea';
import ActionContext from 'studio/context/ActionContext';
import {X} from 'studio/components/StockSVGs';

import * as RecordTargets from 'studio/foundation/recordTargets';
import * as Entity from 'studio/foundation/entity';
import * as Doc from 'studio/foundation/doc';
import * as TargetValue from 'studio/foundation/targetValue';
import * as Targets from 'studio/foundation/targets';
import * as Word from 'studio/foundation/word';

import * as Project from 'studio/state/project';
import {isNonemptyArray} from 'studio/util/types';

type Props = {
  project: Project.t;
  recordName: string;
  doc: Doc.t | undefined;
  children: React.ReactNode;
};

export default function TargetPicker(props: Props) {
  const actionContext = React.useContext(ActionContext);

  const field: string | undefined =
    Project.selectedField(props.project) || undefined;

  const enabled = Project.targetPickingEnabled(props.project) &&
                  props.doc != undefined;

  const recordTargets =
    Project.recordTargets(
      props.project,
      props.recordName);

  const currentTargetValue: TargetValue.t | undefined =
    recordTargets && field
      ? RecordTargets.value(recordTargets, field)
      : undefined;

  const finalizeSelection = React.useCallback(
    (targetValue: TargetValue.t | undefined) => {
      actionContext.dispatchAction({
        type: 'SetTargetValue',
        recordName: props.recordName,

        // XXX ... and the next line.
        field: field as string,
        value: targetValue,
      });
    },
    [field,
     props.recordName,
     props.doc,
     actionContext],
  );

  const onSetSelection = React.useCallback(
    (words: Entity.t[]) => {
      if (isNonemptyArray(words)) {
        finalizeSelection(
          TargetValue.approximateFromUserDragSelection(
            words, props.doc as Doc.t));
      }
    },
    [finalizeSelection,
     props.doc],
  );

  const onToggleSelection = React.useCallback(
    (words: Entity.t[]) => {
      if (isNonemptyArray(words)) {
        finalizeSelection(
          TargetValue.symmetricDifference(
            TargetValue.approximateFromUserDragSelection(
              words, props.doc as Doc.t),
            currentTargetValue));
      }
    },
    [finalizeSelection,
     props.doc,
     currentTargetValue],
  );

  return (
    <DragSelectionArea
      {...{enabled, onSetSelection, onToggleSelection}}
    >
      {props.children}

      {enabled &&
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: 'var(--medium-gutter)',
            transform: 'translate(-50%, 0)',
            padding: 'var(--medium-gutter)',
            background: 'var(--canvas-color)',
            border: 'var(--default-border)',
            borderRadius: 'var(--medium-border-radius)',
            whiteSpace: 'nowrap',
            display: 'flex',
            alignItems: 'baseline',
          }}
          onMouseDown={
            event => {
              event.stopPropagation();
              event.preventDefault();
            }
          }
        >
          <div style={{paddingRight: 'var(--medium-gutter)'}}>
            Select target value for <span className="Field LargeCodeText">{field}</span>
          </div>
          <button
            className="TinyButton"
            style={{
              padding: '3px',
            }}
            onClick={
              event => {
                event.stopPropagation();
                event.preventDefault();
                actionContext.dispatchAction({
                  type: 'SetSelectedField',
                  field: undefined,
                });
              }
            }
          ><X/></button>
        </div>
      }
    </DragSelectionArea>
  );
}
