import React from 'react';

import ModalContext from 'studio/context/ModalContext';
import SessionContext from 'studio/context/SessionContext';
import ActionContext from 'studio/context/ActionContext';
import ProjectContext from 'studio/context/ProjectContext';

import * as Project from 'studio/state/project';

import AppModalBackdrop from 'studio/components/AppModalBackdrop';
import Dialog from 'studio/components/Dialog';
import TableView from 'studio/components/TableView';

import {booleanSort, reversedNumericalSort, stringSort} from 'studio/util/sorting';

type Props = {
  project: Project.t;
};

type RowProps = {
  settingName: string;
  element: JSX.Element;
  valueString: string | undefined; // Just for sorting.
};

export default function(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const sessionContext = React.useContext(SessionContext);
  const actionContext = React.useContext(ActionContext);

  const [settings] = React.useState(props.project.settings);

  const [numSimultaneousModelRuns, setNumSimultaneousModelRuns] =
    React.useState<string>(
      settings.numSimultaneousModelRuns.toString());

  return <AppModalBackdrop>
    <Dialog>
      <div
        style={{
          'display': 'grid',
          'gridTemplateColumns': '1fr',
          'gridTemplateRows': 'min-content 1fr',
          'gridGap': 'var(--large-gutter)',
          'overflow': 'hidden',
          'width': '400px',
          'height': '244px',
        }}
      >
        <TableView
          spec={{
            columns: [
              {
                name: 'Setting',
                fractionalWidth: 1,
                cellContents: (row: RowProps) => row.settingName,
                comparisonFunction: stringSort((row: RowProps) => row.settingName),
              },
              {
                name: 'Value',
                fractionalWidth: 4,
                cellContents: (row: RowProps) => row.element,
                comparisonFunction: stringSort((row: RowProps) => row.valueString),
              },
            ],
            // This should not be keyed on the project UUID.
            // These are app-level settings.
            localStorageSuffix: 'SettingsDialog',
            rowID: (row: RowProps) => row.settingName,
          }}
          rootRows={[
            {
              settingName: 'Maximum number of simultaneous model runs',
              element: (
                <input
                  type="text"
                  value={numSimultaneousModelRuns}
                  onClick={
                    event => event.stopPropagation()
                  }
                  onChange={
                    event => {
                      setNumSimultaneousModelRuns(event.target.value);
                    }
                  }
                />
              ),
              valueString: numSimultaneousModelRuns,
            },
          ]}
        />
      </div>

      <div className="DialogButtons">
        <button
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              modalContext.dispatchModalAction({
                name: 'AskModalToClose',
              });
            }
          }
        >
          Cancel
        </button>

        <button
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();

              const integralNumSimultaneousModelRuns =
                parseInt(numSimultaneousModelRuns);

              if (Number.isNaN(integralNumSimultaneousModelRuns)) {
                alert(`Could not parse maximum number of simultaneous model runs: ${numSimultaneousModelRuns}`);
                return;
              }

              actionContext.dispatchAction({
                type: 'Hack_UpdateProject',
                changes: {
                  settings: {
                    ...settings,
                    numSimultaneousModelRuns: integralNumSimultaneousModelRuns,
                  },
                },
              });

              modalContext.dispatchModalAction({
                name: 'AskModalToClose',
              });
            }
          }
        >
          Ok
        </button>
      </div>
    </Dialog>
  </AppModalBackdrop>;
}
