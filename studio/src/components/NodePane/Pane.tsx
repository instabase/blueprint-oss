import React from 'react';

import * as Doc from 'studio/foundation/doc';
import * as RecordTargets from 'studio/foundation/recordTargets';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as PickBestNode from 'studio/blueprint/pickBestNode';
import * as MergeNode from 'studio/blueprint/mergeNode';

import * as NodeRecordTargets from 'studio/state/nodeRecordTargets';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';

import {Extractions} from 'studio/hooks/useExtractions';
import useResource from 'studio/hooks/useResource';

import SessionContext from 'studio/context/SessionContext';

import BlueprintNodeView from './BlueprintNodeView';
import NodeViewProps from './NodeViewProps';

import loadDoc from 'studio/async/loadDoc';

import './Pane.css';

type Props = {
  project: Project.t;
  extractions: Extractions;
};

export default function NodePane(props: Props) {
  const state = getState(props);
  const content = () => {
    switch (state.state) {
      case 'NoNodeSelected':
        return <div className={
          'CenteredContainer ' +

          // So that this "no node selected" thing occludes TableView headers
          // when everything is dragged so that this pane occupies the
          // entirety of the left half of the window.
          'WithBackground Elevated1'
        }>
          <div className="CenteredText">
            No node selected
          </div>
        </div>;
      case 'PickBestNodeSelected':
      case 'MergeNodeSelected':
      case 'PatternNodeSelected':
        return <BlueprintNodeView {...state.props}/>;
    }
  };

  return content();
}

type NoNodeSelected = {
  state: 'NoNodeSelected';
}

type PatternNodeSelected = {
  state: 'PatternNodeSelected';
  props: NodeViewProps;
}

type PickBestNodeSelected = {
  state: 'PickBestNodeSelected';
  props: NodeViewProps;
}

type MergeNodeSelected = {
  state: 'MergeNodeSelected';
  props: NodeViewProps;
}

type State =
  | NoNodeSelected
  | PatternNodeSelected
  | PickBestNodeSelected
  | MergeNodeSelected
;

function getState(props: Props): State {
  const sessionContext = React.useContext(SessionContext);

  const project = props.project;
  const model = Project.model(props.project);
  const path = props.project.selectedNodeModelPath;
  const node = path ? Model.node(model, path) : undefined;
  const recordName = props.project.selectedRecordName;
  const targets = Project.nodeRecordTargets(props.project, node);
  const extractions = props.extractions;

  const docPromise = recordName
    ? loadDoc(
        project.samplesPath,
        recordName,
        Project.blueprintSettings(props.project),
        sessionContext,
      )
    : undefined;
  const docResource = useResource(docPromise);
  const doc = Resource.finished(docResource);

  if (!path || !node) {
    return {state: 'NoNodeSelected'};
  }

  switch (node.type) {
    case 'pattern':
      return {
        state: 'PatternNodeSelected',
        props: {
          project,
          recordName, doc, targets,
          model, node, path,
          extractions,
        },
      };
    case 'pick_best':
      return {
        state: 'PickBestNodeSelected',
        props: {
          project,
          recordName, doc, targets,
          model, node, path,
          extractions,
        },
      };
    case 'merge':
      return {
        state: 'MergeNodeSelected',
        props: {
          project,
          recordName, doc, targets,
          model, node, path,
          extractions,
        },
      };
  }
}
