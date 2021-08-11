import React from 'react';
import memo from 'memoizee';

import * as BBox from 'studio/foundation/bbox';
import * as RecordTargets from 'studio/foundation/recordTargets';
import * as TargetValue from 'studio/foundation/targetValue';
import * as TargetWord from 'studio/foundation/targetWord';
import * as Word from 'studio/foundation/word';

import * as Rule from 'studio/blueprint/rule';

import * as Project from 'studio/state/project';

import BBoxView from './BBoxView';

import assert from 'studio/util/assert';

import './TargetValuesOverlay.css';

type Props = {
  project: Project.t;
  recordName: string;
  targets: RecordTargets.t;
  targetValuesChecked: boolean;
};

export default function TargetsOverlay(props: Props) {
  const fieldsToShow =
    fieldsForWhichToShowTargetValues(
      props.project,
      props.targetValuesChecked);

  return <>
    {props.targets.assignments
                  .filter(({field, value}) => (fieldsToShow.includes(field)))
                  .map(({field, value}) =>
      <TargetWords
        key={props.recordName + field}
        field={field}
        value={value}
      />)
    }
  </>;
};

type TargetWordsProps = {
  field: string;
  value: TargetValue.t | undefined;
};

function TargetWords(props: TargetWordsProps) {
  const value = props.value;
  if (value == undefined) return <></>;
  const words = value.words;
  if (words == undefined) return <></>;

  return <>
    {words.map((word, index) => (
      <BBoxView
        key={index}
        bbox={word.bbox}
        docBBox={UnitBBox}
        className={'_targetValueWord'}
      />
    ))}
  </>
}

const UnitInterval = {a: 0, b: 1};
const UnitBBox = {ix: UnitInterval, iy: UnitInterval};

export const fieldsForWhichToShowTargetValues = memo(
  function(project: Project.t, checkboxChecked: boolean): string[] {
    switch (project.selectionMode.type) {
      case 'None':
        const recordTargets = Project.selectedRecordTargets(project);
        if (recordTargets && checkboxChecked) {
          return RecordTargets.fields(recordTargets);
        } else {
          return [];
        }
      case 'Field':
        return [project.selectionMode.field];
      case 'Rule':
        const rule = Project.selectedRule(project);
        assert(rule);
        return [...Rule.fields(rule)];
    }
  },
  { max: 10 },
);
