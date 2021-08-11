import React from 'react';
import ActionContext, {Value as ActionContextValue} from 'studio/context/ActionContext';
import TableView, {Spec} from 'studio/components/TableView';
import {Copy, Edit3, FileEarmarkRuled, MergeIcon, PickBestIcon, Trash2} from 'studio/components/StockSVGs';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as Results from 'studio/blueprint/results';

import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';

import {UUID, Nonempty} from 'studio/util/types';
import {reversedNumericalSort, stringSort} from 'studio/util/sorting';

type Props = {
  project: Project.t;
  model: Model.t;
  children?: React.ReactNode;
};

export default function ModelTreeView(props: Props) {
  const actionContext = React.useContext(ActionContext);
  const spec = React.useMemo(
    () => getSpec(props, actionContext),
    [props.project, props.model, actionContext]);
  const root = Model.root(props.model);
  return <TableView
    rootRows={[
      rowProps(root, [root.uuid] as Model.Path, props.project),
    ]}
    spec={spec}
  >
    {props.children}
  </TableView>;
}

type RowProps = {
  node: Node.t;
  path: Model.Path;
  bestExtractionScore: number | undefined;
};

function getSpec(
  props: Props,
  actionContext: ActionContextValue):
    Spec<RowProps>
{
  return {
    columns: [
      {
        name: 'Model nodes',
        fractionalWidth: 3,
        cellContents: (row: RowProps) => (
          <div className="TableView_Cell">
            <div className="TableView_Cell_Contents">
              {Node.displayName(row.node)}
              {<span className="VeryMutedText VerySmallText"> ({formatNodeType(row.node)})</span>}
            </div>
          </div>
        ),
        comparisonFunction: stringSort((row: RowProps) => row.node.name),
      },
      {
        name: 'Score',
        fractionalWidth: 1,
        cellContents: (row: RowProps) => {
          const score = row.bestExtractionScore;

          const className = () => {
            if (score == undefined) {
              return '';
            } else if (score == 1.0) {
              return 'SoftSuccess5of5';
            } else if (score >= 0.8) {
              return 'SoftSuccess4of5';
            } else if (score >= 0.6) {
              return 'SoftSuccess3of5';
            } else if (score >= 0.4) {
              return 'SoftSuccess2of5';
            } else if (score > 0) { // XXX: Should be MIN_FIELD_SCORE.
              return 'SoftSuccess1of5';
            } else {
              console.assert(score == 0);
              return 'SoftSuccess0of5';
            }
          };

          const text = () => {
            if (score == undefined) {
              return '';
            } else {
              return score.toFixed(2);
            }
          };

          return <div className={
            'TableView_Cell ' +
            'TableView_ScoreCell ' +
            'BottomRightAlignedContainer ' +
            className()
          }>
            <div>{text()}</div>
          </div>;
        },
        comparisonFunction: reversedNumericalSort((row: RowProps) => row.bestExtractionScore),
      },
    ],
    localStorageSuffix: `ModelTreeView-${props.project.uuid}`,
    rowID: (row: RowProps) => row.node.uuid,
    rowIsSelected: (row: RowProps): boolean =>
      Project.nodeIsSelected(props.project, row.node),
    hasChildren: (row: RowProps) => Node.hasChildren(row.node),
    getChildren: (row: RowProps) => (
      Node.children(row.node).map(
        child => rowProps(
          child,
          row.path.concat([child.uuid]) as Model.Path,
          props.project
        )
      ) as Nonempty<RowProps[]>
    ),
    childIsSelected: (row: RowProps): boolean =>
      Project.childIsSelected(props.project, row.node),
    onRowSelected: (row: RowProps, parents: RowProps[]) =>
      actionContext.dispatchAction({
        type: 'SetSelectedNode',
        path: row.path,
      }),
    rowClassName: (_: RowProps) => "HiddenButtonsContainer",
    rowChildren: (row: RowProps) =>
      <div className="HiddenButtons">
        {Node.canHaveChildren(row.node) &&
          <button onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              actionContext.dispatchAction({
                type: 'AddChildNode',
                parentNode: row.node as Node.WithChildren,
                parentNodePath: row.path,
                childNode: PatternNode.build(),
                setChildToSelectedNode: false,
              });
            }
          }>
            <FileEarmarkRuled/>
          </button>
        }
        {!Node.canHaveChildren(row.node) &&
         Model.parentNode(props.model, row.path)?.type == 'pick_best' &&
          <button onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              actionContext.dispatchAction({
                type: 'AddChildNode',
                parentNode:
                  Model.parentNode(
                    props.model,
                    row.path) as Node.WithChildren,
                parentNodePath:
                  row.path.slice(0, -1) as Nonempty<UUID[]>,
                childNode: PatternNode.copy(row.node as PatternNode.t),
                setChildToSelectedNode: false,
              });
            }
          }>
            <Copy/>
          </button>
        }
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            actionContext.dispatchAction({
              type: 'PlaceIntoMerge',
              path: row.path,
            });
          }
        }>
          <MergeIcon/>
        </button>
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            actionContext.dispatchAction({
              type: 'PlaceIntoPickBest',
              path: row.path,
            });
          }
        }>
          <PickBestIcon/>
        </button>
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            const result = prompt('Rename', row.node.name || '');
            if (result != null) {
              actionContext.dispatchAction({
                type: 'RenameNode',
                path: row.path,
                name: result == '' ? undefined : result,
              });
            }
          }
        }>
          <Edit3/>
        </button>
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            actionContext.dispatchAction({
              type: 'DeleteNode',
              path: row.path,
            });
          }
        }>
          <Trash2/>
        </button>
      </div>,
  };
}

function formatNodeType(node: Node.t): string {
  switch (node.type) {
    case 'pattern': return 'pattern';
    case 'pick_best': return 'pick best';
    case 'merge': return 'merge';
  }
}

function rowProps(node: Node.t, nodePath: Model.Path, project: Project.t): RowProps {
  return {
    node,
    path: nodePath,
    bestExtractionScore:
      Results.bestExtractionScore(
        Project.resultsForCurrentModelAndSelectedRecordName(
          project),
        node),
  };
}
