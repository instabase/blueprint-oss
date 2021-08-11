import React from 'react';
import Dropdown from 'studio/components/Dropdown';
import {Column} from 'studio/components/Split';

import NodeViewProps from './NodeViewProps';
import FieldsTable from './FieldsTable';
import ChildrenTable from './ChildrenTable';
import RulesTable from './RulesTable';

type Props = NodeViewProps & {};

export default function BlueprintNodeView(props: Props) {
  const children: JSX.Element[] = [];

  children.push(
    <FieldsTable
      key="FieldsTable"
      {...props}
    />);

  if (showChildrenTable(props)) {
    children.push(
      <ChildrenTable
        key="ChildrenTable"
        {...props}
      />
    );
  }

  if (!props.project.settings.annotationMode &&
      props.node.type == 'pattern')
  {
    children.push(
      <RulesTable
        key="RulesTable"
        {...props}
      />
    );
  }

  return (
    <Column {...columnProps(props, children.length)}>
      {children}
    </Column>
  );
}

function showChildrenTable(props: Props) {
  // It's not clear how useful the children table is. Let's disable it for now.
  return false;

  return props.node.type != 'pattern';
}

function columnProps(props: Props, numChildren: number) {
  return {
    localStorageSuffix: `NodePane.BlueprintNodeView-${props.node.uuid}`,
    defaultBreakdown: getDefaultBreakdown(numChildren),
  };
}

const OneWaySplit = [1];
const TwoWaySplit = [1, 1];
const ThreeWaySplit = [1, 1, 1];

function getDefaultBreakdown(numChildren: number) {
  switch (numChildren) {
    case 1: return OneWaySplit;
    case 2: return TwoWaySplit;
    case 3: return ThreeWaySplit;
    default: throw 'Unsupported number of children';
  }
}
