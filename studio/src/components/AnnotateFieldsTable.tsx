import React from 'react';

import * as DocTargets from 'studio/foundation/docTargets';
import * as Entity from 'studio/foundation/entity';
import * as Doc from 'studio/foundation/doc';
import * as TargetValue from 'studio/foundation/targetValue';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import ActionContext from 'studio/context/ActionContext';

import TableView from 'studio/components/TableView';
import TargetValueCell from 'studio/components/TargetValueCell';
import {Plus, Trash2} from 'studio/components/StockSVGs';

import * as Project from 'studio/state/project';

import {booleanSort, stringSort} from 'studio/util/sorting';

type Props = {
  project: Project.t;
};

type RowProps = {
  field: string;
  targetValue: TargetValue.t | undefined;
};

export default function AnnotateFieldsTable(props: Props) {
  const actionContext = React.useContext(ActionContext);

  return (
    <TableView
      rootRows={props.project.targets.schema.map(
        ({field}) => ({
          field,
          targetValue:
            Project.targetValueForSelectedDocName(
              props.project,
              field),
        })
      )}
      spec={{
        columns: [
          {
            name: 'Field',
            fractionalWidth: 1,
            cellContents: (row: RowProps) => (
              <div className="TableView_Cell HiddenButtonsContainer">
                <div className="TableView_Cell_Contents Field">
                  {row.field}
                </div>

                <div className="HiddenButtons">
                  <button
                    onClick={
                      event => {
                        event.stopPropagation();
                        event.preventDefault();
                        const confirmed =
                          confirm(
                            `Warning: this will delete ALL target values for ` +
                            `${row.field}, across ALL docs.\n\n` +
                            `This cannot be undone.\n\n` +
                            `To delete just the target value for this doc, ` +
                            `click the trash icon next to the value itself.`)

                        if (confirmed) {
                          actionContext.dispatchAction({
                            type: 'DeleteFieldFromTargetsSchema',
                            field: row.field,
                          });
                        }
                      }
                    }
                  >
                    <Trash2/>
                  </button>
                </div>
              </div>
            ),
            comparisonFunction: stringSort((row: RowProps) => row.field),
          },
          {
            name: 'Target value',
            fractionalWidth: 1,
            cellContents: (row: RowProps) => {
              const docName = props.project.selectedDocName;
              if (docName != undefined) {
                return (
                  <TargetValueCell
                    {...row}
                    docName={docName}
                    value={row.targetValue}
                    isSelected={Project.selectedField(props.project) == row.field}
                  />
                );
              }
            },
            comparisonFunction: stringSort((row: RowProps) => row.targetValue?.text),
          },
        ],
        localStorageSuffix: `AnnotateFieldsTable-${props.project.uuid}`,
        rowID: (row: RowProps) => row.field,
        rowIsSelected: (row: RowProps) => (
          Project.selectedField(props.project) == row.field
        ),
        onRowSelected: (row: RowProps) => {
          actionContext.dispatchAction({
            type: 'SetSelectedField',
            field: row.field,
          });
        },
        prevRowKeyboardShortcut: {
          key: 'F',
          shiftKey: true,
        },
        nextRowKeyboardShortcut: {
          key: 'F',
        },
      }}
    >
      <div className="CornerButtons">
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            const field = showAddCustomFieldDialog(props.project.targets.schema);
            if (field) {
              actionContext.dispatchAction({
                type: 'AddFieldToTargetsSchema',
                field,
              });
            }
          }
        }>
          <Plus/>
        </button>
      </div>
    </TableView>
  );
}

function showAddCustomFieldDialog(targetsSchema: TargetsSchema.t): string | undefined {
  const field = prompt('New field', 'net_pay');
  if (field) {
    if (TargetsSchema.hasField(targetsSchema, field)) {
      alert(`Field ${field} already exists`);
    } else {
      return field;
    }
  }
}
