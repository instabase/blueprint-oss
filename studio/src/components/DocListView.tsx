import React from 'react';
import ActionContext, {Value as TheActionContext} from 'studio/context/ActionContext';
import SessionContext, {Value as TheSessionContext} from 'studio/context/SessionContext';

import TableView from 'studio/components/TableView';

import * as RecordTargets from 'studio/foundation/recordTargets';

import * as Compare from 'studio/accuracy/compare';

import * as Model from 'studio/blueprint/model';
import * as Results from 'studio/blueprint/results';

import * as RecordRun from 'studio/state/recordRun';
import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';

import shortRecordName from 'studio/util/shortRecordName';
import {preloadResourcesForRecord} from 'studio/util/preloadDocResources';
import {UUID} from 'studio/util/types';
import {booleanSort, reversedNumericalSort, stringSort} from 'studio/util/sorting';
import {Nonempty} from 'studio/util/types';

type Props = {
  project: Project.t;
  recordNames: string[];
  children?: JSX.Element | JSX.Element[];
};

export default function DocListView(props: Props) {
  const actionContext = React.useContext(ActionContext);
  const sessionContext = React.useContext(SessionContext);
  const modelRuns: ModelRun.t[] =
    props.project.modelRuns.length > 0
     ? [props.project.modelRuns[0]].concat(
         props.project.modelRuns.slice(1).filter(
           modelRun => modelRun.pin)).reverse()
     : [];

  const rootRows = rows(props.project, props.recordNames, modelRuns);

  return (
    <TableView
      rootRows={rootRows}
      spec={
        spec(
          props.recordNames,
          props.project,
          actionContext,
          sessionContext,
          modelRuns,
          rootRows.length,
        )
      }
    >
      {props.children}
    </TableView>
  );
}

type RowRecordRunData = RecordRun.t | undefined;

type RowProps = {
  recordName: string;
  isSelected: boolean;
  recordTargets: RecordTargets.t | undefined;
  data: RowRecordRunData[]; // One per visible model run.
};

function spec(
  recordNames: string[],
  project: Project.t,
  actionContext: TheActionContext,
  sessionContext: TheSessionContext,
  modelRuns: ModelRun.t[],
  numRows: number,
) {
  return {
    columns: [
      {
        name: 'Record',
        fractionalWidth: 4,
        cellContents: (row: RowProps) => shortRecordName(row.recordName),
        comparisonFunction: stringSort((row: RowProps) => row.recordName),
        footer: (
          <div className="TableView_Footer">
            ({numRows} records total)
          </div>
        ),
      },
      ...(
        Project.annotationMode(project) ? []
          : modelRunColumns(recordNames, modelRuns, project)
      ),
    ],
    localStorageSuffix: `DocListView-${project.uuid}-${modelRuns.length}`,
    rowID: (row: RowProps) => row.recordName,
    rowIsSelected: (row: RowProps) => row.isSelected,
    onRowSelected: (row: RowProps,
                    parents: RowProps[],
                    prevRow: RowProps | undefined,
                    nextRow: RowProps | undefined) => {
      actionContext.dispatchAction({
        type: 'SetSelectedRecordName',
        recordName: row.recordName,
      });

      for (let sibling of [prevRow, nextRow]) {
        if (sibling != undefined) {
          preloadResourcesForRecord(
            project,
            sibling.recordName,
            sessionContext,
          );
        }
      }
    },
    prevRowKeyboardShortcut: {
      key: 'D',
      shiftKey: true,
    },
    nextRowKeyboardShortcut: {
      key: 'D',
    },
  };
}

function scoreText(score: number | undefined) {
  if (score == undefined) {
    return '';
  } else {
    return score.toFixed(2);
  }
}

function modelScore(rowRecordRunData: RowRecordRunData) {
  const results = rowRecordRunData && getResults(rowRecordRunData);
  return results && Results.bestOverallExtractionScore(results);
}

function FLA(
  row: RowProps,
  rowRecordRunData: RowRecordRunData,
  flaFields: string):
    number | undefined
{
  const extraction =
    rowRecordRunData && rowRecordRunData.type == 'FinishedRecordRun'
     ? Results.bestExtraction(rowRecordRunData.results)
     : undefined;
  return extraction && row.recordTargets &&
    Compare.FLA(extraction, row.recordTargets, flaFields);
}

function FLAText(fla: number | undefined): string {
  if (fla == undefined) {
    return 'N/A';
  } else {
    return fla.toFixed(2);
  }
}

function averageText(average: number | undefined): string {
  if (average == undefined || isNaN(average)){
    return 'N/A';
  } else {
    return average.toFixed(0);
  }
}

function rows(
  project: Project.t,
  recordNames: string[],
  modelRuns: (ModelRun.t | undefined)[]):
    RowProps[]
{
  return recordNames.map(
    recordName => ({
      recordName,
      isSelected: recordName == project.selectedRecordName,
      recordTargets: Project.recordTargets(project, recordName),
      data: modelRuns.map(
        modelRun => (
          modelRun && ModelRun.recordRun(modelRun, recordName)
        )
      ),
    })
  );
}

function EmptyCell() {
  return (
    <div className="TableView_Cell" />
  );
}

function individualModelRunColumns(
  recordNames: string[],
  modelRun: ModelRun.t,
  index: number,
  project: Project.t,
) {
  return [
    {
      name: `Runtime (${modelRun.uuid})`,
      fractionalWidth: 1,
      cellContents: (row: RowProps) => {
        const Cell = ({children}: {children?: string}) => (
          <div className="TableView_Cell">
            <div className="TableView_Cell_Contents RightAlignedText">
              {children}
            </div>
          </div>
        );

        const data = row.data[index];
        if (data == undefined) {
          return <Cell />;
        } else {
          switch (data.type) {
            case 'RequestedRecordRun':
              return <Cell />;
            case 'ActiveRecordRun':
              return <Cell>...</Cell>;
            case 'CanceledRecordRun':
              return <Cell />;
            case 'FailedRecordRun':
              return <Cell>ERR</Cell>;
            case 'FinishedRecordRun':
              if (data.results.runtime_info.timed_out) {
                return <Cell>(T/O)</Cell>;
              } else {
                return <Cell>{data.results.runtime_info.total_ms?.toString()}</Cell>;
              }
          }
        }
      },
      footer: (
        <div className="TableView_Footer RightAlignedText">
          {
            averageText(
              Compare.average(
                modelRun.recordRuns.map(
                  d => RecordRun.results(d)?.runtime_info.total_ms
                ).filter(Boolean) as Nonempty<number>
              )
            )
          }
        </div>
      ),
      comparisonFunction: reversedNumericalSort(
        (row: RowProps) => {
          const data = row.data[index];
          if (data == undefined) {
            return 999999999;
          } else {
            switch (data.type) {
              case 'RequestedRecordRun':
                return 9999999999;
              case 'ActiveRecordRun':
                return 999999999;
              case 'CanceledRecordRun':
                return 99999999;
              case 'FailedRecordRun':
                return 9999999;
              case 'FinishedRecordRun':
                if (data.results.runtime_info.timed_out) {
                  return 999999;
                } else {
                  return data.results.runtime_info.total_ms;
                }
            }
          }
        }
      ),
    },
    {
      name: `Score (${modelRun.uuid})`,
      fractionalWidth: 1,
      cellContents: (row: RowProps) => {
        const score = modelScore(row.data[index]);
        if (score != undefined) {
          return (
            <div className={
              'TableView_Cell ' +
              'TableView_ScoreCell ' +
              'BottomRightAlignedContainer ' +
              `SoftSuccess${colorGradient(score)}of5 `
            }>
              {scoreText(score)}
            </div>
          );
        } else {
          return <EmptyCell />;
        }
      },
      comparisonFunction: reversedNumericalSort(
        (row: RowProps) => modelScore(row.data[index])
      ),
    },
    {
      name: `FLA (${modelRun.uuid})`,
      fractionalWidth: 1,
      cellContents: (row: RowProps) => {
        if (row.data[index]) {
          const theFLA = FLA(row, row.data[index], project.settings.flaFields);
          if (theFLA != undefined) {
            return <div className={
              'TableView_Cell ' +
              'TableView_ScoreCell ' +
              'BottomRightAlignedContainer ' +
              `HardSuccess${colorGradient(theFLA)}of5 `
            }>
              {scoreText(theFLA)}
            </div>;
          } else {
            return (
              <div
                className={
                  'TableView_Cell ' +
                  'TableView_ScoreCell ' +
                  'BottomRightAlignedContainer ' +
                  'HardSuccessUnknown '
                }
              >
                N/A
              </div>
            );
          }
        } else {
          return <EmptyCell />;
        }
      },
      footer: (
        <div className="TableView_Footer RightAlignedText">
          {
            FLAText(
              Compare.averageFLA(
                Project.extractionsAndTargets(
                  recordNames,
                  project.targets,
                  modelRun,
                ),
                project.settings.flaFields,
              )
            )
          }
        </div>
      ),
      comparisonFunction: reversedNumericalSort(
        (row: RowProps) => (
          FLA(
            row,
            row.data[index],
            project.settings.flaFields,
          )
        )
      ),
    },
  ];
}

function getResults(
  rowRecordRunData: RowRecordRunData):
    Results.t | undefined
{
  if (rowRecordRunData?.type == 'FinishedRecordRun') {
    return rowRecordRunData.results;
  }
}

function modelRunColumns(
  recordNames: string[],
  modelRuns: ModelRun.t[],
  project: Project.t,
) {
  return modelRuns.map(
    (modelRun, index) => (
      individualModelRunColumns(
        recordNames,
        modelRun,
        index,
        project,
      )
    )
  ).flat();
}

const colorGradient = (score: number | undefined) => {
  if (score == undefined) {
    return '';
  } else if (score == 1.0) {
    return 5;
  } else if (score >= 0.8) {
    return 4;
  } else if (score >= 0.6) {
    return 3;
  } else if (score >= 0.4) {
    return 2;
  } else if (score > 0) {
    return 1;
  } else {
    console.assert(score == 0);
    return 0;
  }
};
