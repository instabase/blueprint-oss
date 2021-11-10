import React from 'react';
import ModalContext, {Value as TheModalContext} from 'studio/context/ModalContext';
import ActionContext from 'studio/context/ActionContext';
import TableView from 'studio/components/TableView';
import Checkbox from 'studio/components/Checkbox';
import Dropdown from 'studio/components/Dropdown';
import AddFieldDialog from './AddFieldDialog';
import TargetValueCell from 'studio/components/TargetValueCell';
import {Edit2, Plus, Trash2} from 'studio/components/StockSVGs';

import * as DocTargets from 'studio/foundation/docTargets';
import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';
import * as Doc from 'studio/foundation/doc';
import * as TargetValue from 'studio/foundation/targetValue';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import * as Compare from 'studio/accuracy/compare';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as Scoring from 'studio/blueprint/scoring';

import * as NodeDocTargets from 'studio/state/nodeDocTargets';
import * as Project from 'studio/state/project';

import NodeViewProps from './NodeViewProps';
import './FieldsTable.css';

import {booleanSort, numericalSort, stringSort} from 'studio/util/sorting';
import * as TargetExtractions from 'studio/util/targetExtractions';

type Props = NodeViewProps;

export default function FieldsTable(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const actionContext = React.useContext(ActionContext);

  const targetExtraction =
    props.doc &&
    props.targets &&
    TargetExtractions.build(
      props.doc,
      props.targets,
      props.project.targets.schema,
    );

  if (props.node.type == 'pattern' &&
      Node.numFields(props.node) == 0)
  {
    return <div className={
      'CenteredContainer ' +

      // So that this "add fields..." pane occludes TableView headers
      // when everything is dragged so that this pane occupies the
      // entirety of the left half of the window.
      'WithBackground Elevated1'
    }>
      <button
        style={{
          margin: 'var(--huge-gutter)',
        }}
        onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            showAddFieldsDialog(props, modalContext);
          }
        }
      >
        Add fields...
      </button>
    </div>;
  }

  return <TableView
    rootRows={Node.fieldTypePairs(props.node).map(
      ([field, type]) => ({
        field,
        type,
        targetValue:
          props.targets &&
          DocTargets.value(
            props.targets,
            field),
        extractedValue:
          Scoring.value(
            props.extractions.selected,
            field),
        targetExtractionValue:
          targetExtraction &&
          Extraction.value(
            targetExtraction,
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
                {false && props.node.type == 'pattern' &&
                  <button onClick={event => {
                    event.stopPropagation();
                    event.preventDefault();
                    const newName = prompt('Rename field ' + row.field, row.field);
                    if (newName != null && newName != '' && newName != row.field) {
                      if (Model.illegalToAddFieldNames(props.model, props.path).has(newName)) {
                        alert('Cannot use that field name. ' +
                              'Either a field by that name already exists in this pattern, ' +
                              'or a field by this name exists in a pattern which could ' +
                              'be merged with this one elsewhere in the model.');
                      } else {
                        actionContext.dispatchAction({
                          type: 'RenameField',
                          node: props.node as PatternNode.t,
                          path: props.path,
                          oldName: row.field,
                          newName: newName,
                        });
                      }
                    }
                  }}>
                    <Edit2/>
                  </button>
                }
                
                {canEditFields(props.node) &&
                  <button onClick={event => {
                    event.stopPropagation();
                    event.preventDefault();
                    actionContext.dispatchAction({
                      type: 'RemoveField',
                      node: props.node as PatternNode.t,
                      path: props.path,
                      field: row.field,
                    })}}
                  >
                    <Trash2/>
                  </button>
                }
              </div>
            </div>
          ),
          comparisonFunction: stringSort((row: RowProps) => row.field),
        },
        {
          name: 'Type',
          fractionalWidth: 1,
          cellContents: (row: RowProps) => (
            <Dropdown<Entity.Type>
              className="TableView_FullCell EntityType VerySmallText"
              options={Entity.Types}
              selected={row.type}
              stringify={s => s}
              onSelected={type => {
                actionContext.dispatchAction({
                  type: 'SetFieldType',
                  field: row.field,
                  newType: type,
                  isLabel: Project.isLabel(props.project, row.field) == true,
                });
              }}
            />
          ),
          comparisonFunction: stringSort((row: RowProps) => row.type),
        },
        {
          name: 'Label',
          element: (
            <div className="TableView_Header CenteredText TooltipContainer">
              ↦
              <div className="Tooltip _top">
                Treat this field as an anchor / label.
                This is only used for rule generation.<br /><br />
                You should usually
                set this for fields having fixed text
                values within a particular pattern,
                such as "Employee name:" or "Period Begin Date",
                but not for text fields where the text varies
                from doc to doc, such as addresses.
              </div>
            </div>
          ),
          fractionalWidth: 0.2,
          cellContents: (row: RowProps) => (
            <div className="TableView_Cell CenteredText">
              {row.type == 'Text' && TargetsSchema.hasField(props.project.targets.schema, row.field) &&
                <Checkbox
                  checked={Project.isLabel(props.project, row.field) == true}
                  setChecked={
                    newValue => {
                      actionContext.dispatchAction({
                        type: 'SetFieldType',
                        field: row.field,
                        newType: row.type,
                        isLabel: newValue,
                      });
                    }
                  }
                />
              }
            </div>
          ),
          comparisonFunction: booleanSort(
            (row: RowProps) => Project.isLabel(props.project, row.field)
          ),
        },
        {
          name: 'Found target extraction',
          element: (
            <div className="TableView_Header CenteredText TooltipContainer">
              ⦿
              <div className="Tooltip _top">
                Found a generated entity matching given target value.
              </div>
            </div>
          ),
          fractionalWidth: 0.2,
          cellContents: (row: RowProps) => {
            if (cannotFindEntityForPositionedTargetValue(row, targetExtraction)) {
              return (
                <div className="TableView_Cell TooltipContainer">
                  <div className="CenterInParent">❌</div>
                  <div className="Tooltip _right_hangDown">
                    Cannot find entity of type <span className="EntityType">{TargetsSchema.type(props.project.targets.schema, row.field)}</span> matching <span className="StringLiteral">{row.targetValue?.text}</span>.
                  </div>
                </div>
              );
            } else if (targetValueHasNoGeometryInformation(row)) {
              return (
                <div className="TableView_Cell TooltipContainer">
                  <div className="CenterInParent">⚠️</div>
                  <div className="Tooltip _right_hangDown">
                    Target value has no geometry / bounding box information.<br /><br />
                    This target value will be used for FLA/STP calculation,
                    but cannot be used for model training or debugging.
                  </div>
                </div>
              );
            }
          },
          comparisonFunction: numericalSort(
            (row: RowProps) => {
              if (cannotFindEntityForPositionedTargetValue(row, targetExtraction)) {
                return 2;
              } else if (targetValueHasNoGeometryInformation(row)) {
                return 1;
              } else {
                return 0;
              }
            }
          ),
        },
        {
          name: 'Target value',
          fractionalWidth: 1.5,
          cellContents: (row: RowProps) => {
            if (props.docName != undefined && props.targets) {
              if (!TargetsSchema.hasField(props.project.targets.schema, row.field)) {
                return (
                  <div className="TableView_Cell">
                    <div className="TableView_Cell_Contents MutedText SlightlySmallText">
                      (not in schema)
                    </div>
                  </div>
                );
              } else {
                return (
                  <TargetValueCell
                    {...row}
                    docName={props.docName}
                    value={row.targetValue}
                    isSelected={Project.selectedField(props.project) == row.field}
                  />
                );
              }
            }
          },
          comparisonFunction: stringSort((row: RowProps) => row.targetValue?.text),
        },
        {
          name: 'Model results',
          element: <div className={
            'TableView_Header ' +
            'NodePane_FieldsTable_ModelResultsHeader ' +
            'TooltipContainer'
          }>
            <div className="ElidingText">Model results{
              props.node.name && <span> ({props.node.name})</span>
            }</div>
            <Dropdown {...props.extractions} />

            <div className="Tooltip _top">
              Model output for this node{
                props.node.name && <span> ({props.node.name})</span>
              }.
              These values may differ from
              the overall model results for this doc.
              To see the overall model results,
              select the model's root node.
            </div>
          </div>,
          fractionalWidth: 1.5,
          cellContents: (row: RowProps) => {
            const Text = () => {
              if (props.extractions.selected == undefined) {
                return null;
              } else {
                const extractedText = row.extractedValue?.text;
                if (extractedText == undefined) {
                  return <span className="MutedText">(null)</span>;
                } else {
                  return <span className="EntityText">{extractedText}</span>;
                }
              }
            };

            return (
              <div className="TableView_Cell">
                <div className="TableView_Cell_Contents">
                  <Text />
                </div>
              </div>
            );
          },
          comparisonFunction: stringSort((row: RowProps) => row.extractedValue?.text),
        },
        {
          name: 'Match',
          element: (
            <div className="TableView_Header CenteredText TooltipContainer">
              ✓
              <div className="Tooltip _top">
                Target and extracted values match.
              </div>
            </div>
          ),
          fractionalWidth: 0.2,
          cellContents: (row: RowProps) => {
            const matchResult = match(row);
              
            const className = () => {
              const prefix =
                'TableView_Cell ' +
                'TableView_ScoreCell ' +
                'CenteredContainer ';
              if (!props.extractions.selected) {
                return prefix;
              } else if (matchResult == 'PositiveMatchResult') {
                return prefix + 'HardSuccess5of5';
              } else if (matchResult == 'NegativeMatchResult') {
                return prefix + 'HardSuccess0of5';
              } else {
                return prefix + 'HardSuccessUnknown';
              }
            };
              
            const text = () => {
              if (!props.extractions.selected) {
                return '';
              } else if (matchResult == 'PositiveMatchResult') {
                return '✓';
              } else if (matchResult == 'NegativeMatchResult') {
                return '✘';
              } else {
                return '';
              }
            };

            return <div className={className()}>
              {text()}
            </div>;
          },
          comparisonFunction: booleanSort(
            (row: RowProps) => Compare.toBoolean(match(row))
          ),
        },
      ],
      localStorageSuffix: `NodePane.FieldsTable-${props.node.type}`,
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
    {canEditFields(props.node) &&
      <div className="CornerButtons">
        <button onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            showAddFieldsDialog(props, modalContext);
          }
        }>
          <Plus/>
        </button>
      </div>
    }
  </TableView>;
}

type RowProps = {
  field: string;
  type: Entity.Type;
  targetValue: TargetValue.t | undefined;
  extractedValue: Entity.t | undefined;
  targetExtractionValue: Entity.t | undefined;
};

function canEditFields(node: Node.t): boolean {
  return node.type == 'pattern';
}

function fieldsFromTargets(
  docTargets: DocTargets.t | undefined):
    Record<string, Entity.Type>
{
  if (!docTargets) {
    return {};
  } else {
    const result: Record<string, Entity.Type> = {}
    docTargets.assignments.forEach(
      ({field}) => result[field] = Entity.DefaultType
    );
    return result;
  }
}

function showAddFieldsDialog(
  props: Props,
  modalContext: TheModalContext):
    void
{
  const fields: Record<string, Entity.Type> = {
    ...fieldsFromTargets(Project.docTargets(props.project, props.docName)),
    ...TargetsSchema.fieldToTypeMap(props.project.targets?.schema || []),
  };

  modalContext.dispatchModalAction({
    name: 'ShowModal',
    modal: <AddFieldDialog
      model={props.model}
      node={props.node as PatternNode.t}
      path={props.path}
      fields={fields}
      annotationMode={false}
    />,
  });
}

function match(row: RowProps) {
  return Compare.match(
    row.extractedValue,
    row.targetValue,
  );
}

function targetValueHasNoGeometryInformation(row: RowProps): boolean {
  return row.targetValue != undefined &&
         TargetValue.isNonNull(row.targetValue) &&
         !TargetValue.isPositioned(row.targetValue);
}

function cannotFindEntityForPositionedTargetValue(
  row: RowProps,
  targetExtraction: Extraction.t | undefined):
    boolean
{
  return row.targetValue != undefined &&
         TargetValue.isPositioned(row.targetValue) &&
         targetExtraction != undefined &&
         row.targetExtractionValue == undefined;
}
