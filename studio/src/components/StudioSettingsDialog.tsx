import React from 'react';

import ModalContext from 'studio/context/ModalContext';
import SessionContext from 'studio/context/SessionContext';

import AppModalBackdrop from 'studio/components/AppModalBackdrop';
import Dialog from 'studio/components/Dialog';
import TableView from 'studio/components/TableView';

import {booleanSort, reversedNumericalSort, stringSort} from 'studio/util/sorting';

type Props = {};

type RowProps = {
  settingName: string;
  element: JSX.Element;
  valueString: string | undefined; // Just for sorting.
};

export default function(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const sessionContext = React.useContext(SessionContext);

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
                name: 'AskModalToClose'
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
