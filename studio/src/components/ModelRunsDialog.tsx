import memo from 'memoizee';
import React from 'react';

import ModalContext from 'studio/context/ModalContext';
import ActionContext from 'studio/context/ActionContext';
import ProjectContext from 'studio/context/ProjectContext';

import TableView from 'studio/components/TableView';
import {Trash2} from 'studio/components/StockSVGs';
import Checkbox from 'studio/components/Checkbox';
import Dialog from 'studio/components/Dialog';
import Dropdown from 'studio/components/Dropdown';
import AppModalBackdrop from 'studio/components/AppModalBackdrop';

import * as DocRun from 'studio/state/docRun';
import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';

import {booleanSort, numericalSort, reversedNumericalSort, stringSort} from 'studio/util/sorting';
import {humanReadableFileSize} from 'studio/util/debug';

type Props = {};

export default function ModelRunsDialog(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const actionContext = React.useContext(ActionContext);

  const project = React.useContext(ProjectContext).project;

  const close = () =>
    modalContext.dispatchModalAction({
      name: 'AskModalToClose'
    });

  if (project == undefined) {
    throw 'No project';
  }

  return <AppModalBackdrop>
    <Dialog>
      <div
        style={{
          'display': 'grid',
          'gridTemplateColumns': '1fr',
          'gridTemplateRows': 'min-content 1fr',
          'gridGap': 'var(--large-gutter)',
          'overflow': 'hidden',
          'width': '700px',
          'height': '544px',
        }}
      >
        <TableView
          spec={{
            columns: [
              {
                name: 'ID',
                fractionalWidth: 5,
                cellContents: (row: ModelRun.t) => (
                  <div className="TableView_Cell HiddenButtonsContainer">
                    <div className="TableView_Cell_Contents">
                      {row.uuid}
                    </div>

                    <div className="HiddenButtons">
                      <button
                        onClick={
                          event => {
                            event.stopPropagation();
                            event.preventDefault();

                            actionContext.dispatchAction({
                              type: 'Hack_UpdateProject',
                              changes: {
                                modelRuns: project.modelRuns.filter(
                                  modelRun => modelRun.uuid != row.uuid
                                ),
                              },
                            });
                          }
                        }
                      >
                        <Trash2/>
                      </button>
                    </div>
                  </div>
                ),
                comparisonFunction: stringSort((row: ModelRun.t) => row.uuid),
              },
              {
                name: 'Started',
                fractionalWidth: 3,
                cellContents: (row: ModelRun.t) => (
                  new Date(row.startTime_ms).toLocaleString()
                ),
                comparisonFunction: reversedNumericalSort(
                  (row: ModelRun.t) => row.startTime_ms,
                ),
              },
              {
                name: 'Keep',
                element: (
                  <div className="TableView_Header CenteredText">
                    Keep
                  </div>
                ),
                fractionalWidth: 1,
                cellContents: (row: ModelRun.t) => (
                  <div className="TableView_Cell CenteredText">
                    <Checkbox
                      checked={row.keep}
                      setChecked={
                        newValue => {
                          actionContext.dispatchAction({
                            type: 'UpdateModelRun',
                            uuid: row.uuid,
                            keep: newValue,
                            pin: row.pin,
                          });
                        }
                      }
                    />
                  </div>
                ),
                comparisonFunction: booleanSort((row: ModelRun.t) => row.keep),
              },
              {
                name: 'Pin',
                element: (
                  <div className="TableView_Header CenteredText">
                    Pin
                  </div>
                ),
                fractionalWidth: 1,
                cellContents: (row: ModelRun.t) => (
                  <div className="TableView_Cell CenteredText">
                    <Checkbox
                      checked={row.pin}
                      setChecked={
                        newValue => {
                          actionContext.dispatchAction({
                            type: 'UpdateModelRun',
                            uuid: row.uuid,
                            keep: row.keep,
                            pin: newValue,
                          });
                        }
                      }
                    />
                  </div>
                ),
                comparisonFunction: booleanSort((row: ModelRun.t) => row.pin),
              },
              {
                name: 'Size',
                element: (
                  <div className="TableView_Header RightAlignedText">
                    Size
                  </div>
                ),
                fractionalWidth: 1,
                cellContents: (row: ModelRun.t) => (
                  <div className="TableView_Cell">
                    <div className="TableView_Cell_Contents RightAlignedText">
                      {humanReadableFileSize(memoizeStringify(row).length)}
                    </div>
                  </div>
                ),
                comparisonFunction: numericalSort(
                  (row: ModelRun.t) => memoizeStringify(row).length
                ),
              },
            ],
            localStorageSuffix: `ModelRunsDialog-${project.uuid}`,
            rowID: (row: ModelRun.t) => row.uuid,
          }}
          rootRows={project.modelRuns}
        />
      </div>

      <div className="DialogButtons">
        <button onClick={event => {
          event.stopPropagation();
          event.preventDefault();
          close();
        }}>
          Ok
        </button>
      </div>
    </Dialog>
  </AppModalBackdrop>;
}

const memoizeStringify = memo(
  function(o: object): string {
    return JSON.stringify(o);
  },
  { max: 500 },
);
