import React from 'react';
import Checkbox, {Props as CheckboxProps} from 'studio/components/Checkbox';
import {SelectionMode} from 'studio/state/project';
import {Options} from 'studio/hooks/useOptions';

type Props = {
  selectionMode: SelectionMode;
  entityTypeOptions: Options;
  targetValuesOption: CheckboxProps;
  extractedValuesOption: CheckboxProps;
};

export default function EntityTypePicker(props: Props) {
  const typeNames =
    [...Object.keys(props.entityTypeOptions)];

  const allChecked =
    typeNames.every(typeName => props.entityTypeOptions[typeName].checked) &&
    (props.targetValuesOption.disabled || props.targetValuesOption.checked) &&
    (props.extractedValuesOption.disabled || props.extractedValuesOption.checked);

  const toggleAll = () => {
    if (allChecked) {
      typeNames.forEach(
        typeName => props.entityTypeOptions[typeName].setChecked(false));
      if (!props.targetValuesOption.disabled) {
        props.targetValuesOption.setChecked(false);
      }
      if (!props.extractedValuesOption.disabled) {
        props.extractedValuesOption.setChecked(false);
      }
    } else {
      typeNames.forEach(
        typeName => props.entityTypeOptions[typeName].setChecked(true));
      if (!props.targetValuesOption.disabled) {
        props.targetValuesOption.setChecked(true);
      }
      if (!props.extractedValuesOption.disabled) {
        props.extractedValuesOption.setChecked(true);
      }
    }
  };

  const entityTypeSelectionDisabled = props.selectionMode.type != 'None';

  return (
    <div
      style={{
        position: 'absolute',
        background: 'var(--canvas-color)',
        fontSize: 'var(--small-font-size)',
        right: 'var(--medium-gutter)',
        bottom: 'var(--medium-gutter)',
        padding: 'var(--small-gutter)',
        border: 'var(--default-border)',
        borderRadius: 'var(--medium-border-radius)',
        display: 'grid',
        gridTemplateColumns: 'min-content min-content',
        gridGap: 'var(--tiny-gutter) var(--checkbox-label-gap)',
        alignItems: 'center',
      }}
    >
      {typeNames.map(typeName =>
        <Row
          key={typeName}
          label={
            <span
              className={
                'EntityType ' +
                (entityTypeSelectionDisabled ? 'VeryMutedText' : '')
              }
            >
              {typeName}
            </span>
          }
          disabled={entityTypeSelectionDisabled}
          checked={
            !entityTypeSelectionDisabled &&
            props.entityTypeOptions[typeName].checked
          }
          setChecked={props.entityTypeOptions[typeName].setChecked}
        />
      )}

      <Row
        label={
          <span
            className={
              props.targetValuesOption.disabled ||
              entityTypeSelectionDisabled
                ? 'VeryMutedText'
                : ''}
          >Target values</span>
        }
        disabled={
          props.targetValuesOption.disabled ||
          entityTypeSelectionDisabled}
        checked={
          entityTypeSelectionDisabled
            ? false
            : props.targetValuesOption.checked}
        setChecked={props.targetValuesOption.setChecked}
      />

      <Row
        label={
          <span
            className={
              props.extractedValuesOption.disabled ||
              entityTypeSelectionDisabled
                ? 'VeryMutedText'
                : ''}
          >Extracted values</span>
        }
        disabled={
          props.extractedValuesOption.disabled ||
          entityTypeSelectionDisabled}
        checked={
          entityTypeSelectionDisabled
            ? false
            : props.extractedValuesOption.checked}
        setChecked={props.extractedValuesOption.setChecked}
      />

      <Row
        label={
          <span className="MutedText">(Toggle all)</span>
        }
        disabled={entityTypeSelectionDisabled}
        checked={
          entityTypeSelectionDisabled
            ? false
            : allChecked}
        setChecked={toggleAll}
      />
    </div>
  );
}

type RowProps = CheckboxProps & {
  label: React.ReactNode;
};

function Row(props: RowProps) {
  const {label, ...checkboxProps} = props;
  return <>
    <Checkbox {...checkboxProps} />

    <div
      className="DisallowUserSelection NoWrap"
      onClick = {
        event => {
          event.stopPropagation();
          event.preventDefault();
          props.setChecked(!props.checked);
        }
      }
    >
      {label}
    </div>
  </>;
}
