import React from 'react';
import ModelTreeView from './ModelTreeView';
import * as Project from 'studio/state/project';

type Props = {
  project: Project.t;
};

export default function ModelTreePane(props: Props) {
  const model = Project.model(props.project);
  
  return (
    <ModelTreeView
      {...props}
      model={model}
    />
  );
}
