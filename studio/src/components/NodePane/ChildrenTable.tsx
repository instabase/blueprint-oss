import React from 'react';
import ModalContext from 'studio/context/ModalContext';
import ActionContext from 'studio/context/ActionContext';
import TableView from 'studio/components/TableView';
import {MagicWand, Plus, Trash2} from 'studio/components/StockSVGs';

import * as RecordTargets from 'studio/foundation/recordTargets';
import * as Doc from 'studio/foundation/doc';
import * as TargetValue from 'studio/foundation/targetValue';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as Results from 'studio/blueprint/results';

import * as NodeRecordTargets from 'studio/state/nodeRecordTargets';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';

import NodeViewProps from './NodeViewProps';
import {Nonempty} from 'studio/util/types';
import {reversedNumericalSort, stringSort} from 'studio/util/sorting';

type Props = NodeViewProps;

type RowProps = {
  child: Node.t;
  childPath: Model.Path;
  bestExtractionScore: number | undefined;
};

export default function ChildrenTable(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const actionContext = React.useContext(ActionContext);
  return <TableView
    rootRows={Node.children(props.node).map(child => ({
      child,
      childPath: props.path.concat([child.uuid]) as Nonempty<string[]>,
      bestExtractionScore:
        Results.bestExtractionScore(
          Project.resultsForCurrentModelAndSelectedRecordName(
            props.project),
          child),
    }))}
    spec={{
      columns: [
        {
          name:
            props.node.type == 'merge'
              ? 'Child nodes to merge'
              : 'Child nodes to pick from',
          fractionalWidth: 3,
          cellContents: (row: RowProps) => (
            <div className="TableView_Cell HiddenButtonsContainer">
              <div className="TableView_Cell_Contents">
                {Node.displayName(row.child)}
              </div>

              <div className="HiddenButtons">
                <button
                  onClick={
                    event => {
                      event.stopPropagation();
                      event.preventDefault();
                      actionContext.dispatchAction({
                        type: 'DeleteNode',
                        path: row.childPath,
                      });
                    }
                  }
                >
                  <Trash2/>
                </button>
              </div>
            </div>
          ),
          comparisonFunction: stringSort((row: RowProps) => row.child.name),
        },
        {
          name: 'Score',
          cellContents: (row: RowProps) => formatScore(row.bestExtractionScore),
          fractionalWidth: 1,
          comparisonFunction: reversedNumericalSort((row: RowProps) => row.bestExtractionScore),
        },
      ],
      localStorageSuffix: `NodePane.ChildrenTable-${props.project.uuid}`,
      rowID: (row: RowProps) => row.child.uuid,
    }}
  >
    <div className="CornerButtons">
      <button onClick={event => {
        event.stopPropagation();
        event.preventDefault();
        actionContext.dispatchAction({
          type: 'AddChildNode',
          parentNode: props.node as Node.WithChildren,
          parentNodePath: props.path,
          childNode: PatternNode.build(),
          setChildToSelectedNode: false,
        })}}
      >
        <Plus/>
      </button>
    </div>
  </TableView>;
}

function formatScore(score: number | undefined): string {
  if (score == undefined) {
    return '';
  } else {
    return score.toFixed(2);
  }
}
