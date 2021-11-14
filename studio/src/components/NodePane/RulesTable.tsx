import React from 'react';
import ModalContext, {Value as TheModalContext} from 'studio/context/ModalContext';
import SessionContext, {Value as TheSessionContext} from 'studio/context/SessionContext';
import ActionContext, {Value as TheActionContext} from 'studio/context/ActionContext';
import AppModalBackdrop from 'studio/components/AppModalBackdrop';
import TableView from 'studio/components/TableView';
import {Edit2, Plus, Trash2, MagicWand} from 'studio/components/StockSVGs';
import EditRuleDialog from './EditRuleDialog';

import * as Doc from 'studio/foundation/doc';
import * as DocTargets from 'studio/foundation/docTargets';
import * as Extraction from 'studio/foundation/extraction';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as Predicate from 'studio/blueprint/predicate';
import * as Rule from 'studio/blueprint/rule';
import * as Scoring from 'studio/blueprint/scoring';
import * as WiifNode from 'studio/blueprint/wiifNode';

import * as NodeDocTargets from 'studio/state/nodeDocTargets';
import * as Project from 'studio/state/project';
import * as Resource from 'studio/state/resource';
import * as Settings from 'studio/state/settings';

import synthesis from 'studio/async/synthesis';
import wiif from 'studio/async/wiif';

import * as TargetExtractions from 'studio/util/targetExtractions';

import useResource from 'studio/hooks/useResource';

import NodeViewProps from './NodeViewProps';

import assert from 'studio/util/assert';
import {reversedNumericalSort, stringSort} from 'studio/util/sorting';

type Props = NodeViewProps;

export default function RulesTable(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const sessionContext = React.useContext(SessionContext);
  const actionContext = React.useContext(ActionContext);

  const targetExtraction =
    props.doc &&
    props.targets &&
    TargetExtractions.build(
      props.doc,
      props.targets,
      props.project.targets.schema);

  const wiifPromise = 
    props.docName && props.doc && targetExtraction
    ? wiif(
        props.doc,
        props.node,
        targetExtraction,
        Project.blueprintSettings(props.project),
        sessionContext,
      )
    : undefined;

  const wiifResource = useResource(wiifPromise);
  const wiifNode = Resource.finished(wiifResource);

  const canAddConstraints =
    Node.numFields(props.node) > 0;

  const runSynthesis = React.useMemo(() => {
    const patternNode =
      props.node.type == 'pattern'
        ? props.node
        : undefined;

    const targetExtraction =
      patternNode &&
      props.doc &&
      props.targets &&
      TargetExtractions.buildComplete(
        props.doc,
        patternNode,
        props.targets,
        props.project.targets.schema,
      );

    if (
      Node.numFields(props.node) > 0 &&
      props.docName != undefined &&
      props.doc != undefined &&
      props.targets != undefined &&
      targetExtraction != undefined
    ) {
      const targetsSchema = TargetsSchema.filter(
        props.project.targets.schema,
        field => (
          DocTargets.hasValue(
            props.targets as DocTargets.t,
            field
          )
        ),
      );

      return () => reallyRunSynthesis(
        props.node,
        props.path,
        props.docName as string,
        props.doc as Doc.t,
        targetExtraction,
        targetsSchema,
        Project.blueprintSettings(props.project),
        modalContext,
        sessionContext,
        actionContext,
      );
    }
  }, [
    props.node,
    props.path,
    props.docName,
    props.doc,
    props.targets,
    props.project.targets.schema,
    modalContext,
    sessionContext,
    actionContext,
  ]);

  if (props.node.type == 'pattern' &&
      Node.numRules(props.node) == 0)
  {
    return (
      <div className="CenteredStack">
        <button
          disabled={!canAddConstraints}
          style={{
            margin: 'var(--medium-gutter)',
          }}
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              showAddConstraintDialog(props, modalContext, actionContext);
            }
          }
        >
          Add constraints...
        </button>
        <button
          disabled={runSynthesis == undefined}
          style={{
            margin: 'var(--medium-gutter)',
          }}
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              assert(runSynthesis != undefined);
              runSynthesis();
            }
          }
        >
          Auto-generate constraints...
        </button>
      </div>
    );
  }

  function makeRow(rule: Rule.t): RowProps {
    return {
      rule,
      wiifScore: wiifScore(rule, wiifNode),
      ruleScore: ruleScore(props, rule),
    };
  }

  return <TableView
    rootRows={props.node.rules.map(makeRow)}
    spec={{
      columns: [
        {
          name: 'Constraint',
          fractionalWidth: 2,
          cellContents: (row: RowProps, expanded: boolean) => (
            <div className="TableView_Cell HiddenButtonsContainer">
              <div className="TableView_Cell_Contents_NoHoverReveal">
                <RuleView
                  key={row.rule.uuid}
                  rule={row.rule}
                  expanded={expanded}
                />
              </div>

              <div className="HiddenButtons _topAligned">
                <button onClick={event => {
                  event.stopPropagation();
                  event.preventDefault();
                  modalContext.dispatchModalAction({
                    name: 'ShowModal',
                    modal: <EditRuleDialog
                      node={props.node}
                      rule={row.rule}
                      onRuleFinalized={(rule: Rule.t) =>
                        actionContext.dispatchAction({
                          type: 'ReplaceRule',
                          node: props.node,
                          path: props.path,
                          oldRule: row.rule,
                          newRule: rule,
                        })
                      }
                    />,
                  })}}
                >
                  <Edit2/>
                </button>
                <button onClick={event => {
                  event.stopPropagation();
                  event.preventDefault();
                  actionContext.dispatchAction({
                    type: 'RemoveRule',
                    node: props.node,
                    path: props.path,
                    rule: row.rule,
                  })}}
                >
                  <Trash2/>
                </button>
              </div>
            </div>
          ),
          comparisonFunction: stringSort(
            (row: RowProps) => Rule.displayName(row.rule)
          ),
        },
        {
          name: 'Match with target values',
          fractionalWidth: 1,
          cellContents: (row: RowProps) => {
            const score = row.wiifScore;

            const docTargets = props.targets;
            const anyFieldUnknown =
              docTargets == undefined ||
              !DocTargets.hasAllValues(
                docTargets, [...Rule.fields(row.rule)]);

            const className = () => {
              if (anyFieldUnknown) {
                return 'HardSuccessUnknown';
              } else if (score == undefined) {
                return 'HardSuccessUnknown'; // Loading. (I think.)
              } else if (score == 1.0) {
                return 'HardSuccess5of5';
              } else if (score >= 0.8) {
                return 'HardSuccess4of5';
              } else if (score >= 0.6) {
                return 'HardSuccess3of5';
              } else if (score >= 0.4) {
                return 'HardSuccess2of5';
              } else if (score > 0.1) { // XXX hack?
                return 'HardSuccess1of5';
              } else {
                return 'HardSuccess0of5';
              }
            };

            const text = () => {
              if (anyFieldUnknown) {
                return '(unknown)';
              } else if (score == undefined) {
                return ''; // Loading. (I think.)
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
          comparisonFunction: reversedNumericalSort((row: RowProps) => row.wiifScore),
        },
        {
          name: 'Score',
          fractionalWidth: 1,
          cellContents: (row: RowProps) => {
            const score = row.ruleScore;

            const className = () => {
              if (!props.extractions.selected) {
                return '';
              } else if (!score) {
                return 'HardSuccessUnknown';
              } else if (score == 1.0) {
                return 'HardSuccess5of5';
              } else if (score >= 0.8) {
                return 'HardSuccess4of5';
              } else if (score >= 0.6) {
                return 'HardSuccess3of5';
              } else if (score >= 0.4) {
                return 'HardSuccess2of5';
              } else if (score > 0) {
                return 'HardSuccess1of5';
              } else {
                console.assert(score == 0);
                return 'HardSuccess0of5';
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
              {text()}
            </div>;
          },
          comparisonFunction: reversedNumericalSort((row: RowProps) => row.ruleScore),
        },
      ],
      localStorageSuffix: `NodePane.RulesTable-${props.project.uuid}`,
      rowID: (row: RowProps) => row.rule.uuid,
      rowIsSelected: (row: RowProps): boolean => (
        Project.ruleIsSelected(props.project, row.rule)
      ),
      onRowSelected: (row: RowProps) => {
        actionContext.dispatchAction({
          type: 'SetSelectedRule',
          path: props.path,
          rule: row.rule,
        })
      },
      hasChildren: (row: RowProps) => (
        row.rule.type != 'atom' &&
        row.rule.rules.length > 0
      ),
      getChildren: (row: RowProps) => (
        (row.rule as Rule.Connective).rules.map(makeRow)
      ),
      rowsCollapsedByDefault: true,
    }}
  >
    <div className="CornerButtons">
      <button
        disabled={!canAddConstraints}
        onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            showAddConstraintDialog(props, modalContext, actionContext);
          }
        }
      >
        <Plus />
      </button>
      <button
        disabled={runSynthesis == undefined}
        onClick={event => {
          event.stopPropagation();
          event.preventDefault();
          assert(runSynthesis != undefined);
          runSynthesis();
        }}
      >
        <MagicWand />
      </button>
    </div>
  </TableView>;
}

type RowProps = {
  rule: Rule.t;
  wiifScore: number | undefined;
  ruleScore: number | undefined;
};

// Implementation

type RuleViewProps = {
  rule: Rule.t;
  expanded: boolean;
};

function RuleView({rule, expanded}: RuleViewProps) {
  if (rule.type == 'atom') {
    return <AtomView rule={rule} />
  } else {
    return (
      <div className="AllowLineBreaks HangingIndent">
        <span className="Predicate">
          {Rule.displayName(rule)}
        </span>
        {!expanded &&
          <>
            <br />
            {Rule.fieldsInOrder(rule).map(
              (field, index) => (
                <React.Fragment key={field + index.toString()}>
                  <span className="Field">{field}</span>
                  <br />
                </React.Fragment>
              )
            )}
          </>
        }
      </div>
    );
  }
}

type AtomViewProps = {
  rule: Rule.Atom;
};

function AtomView({rule}: AtomViewProps) {
  if (rule.predicate.name == 'text_equals') {
    return (
      <TextEqualsView
        rule={rule}
        predicate={rule.predicate}
      />
    );
  } else if (rule.fields.length == 1) {
    return (
      <div className="AllowLineBreaks HangingIndent">
        <span className="Predicate">
          {Rule.displayName(rule)}
        </span> <span className="Field">
          {rule.fields[0] as string}
        </span>
      </div>
    );
  } else {
    return (
      <div className="AllowLineBreaks HangingIndent">
        <span className="Predicate">
          {Rule.displayName(rule)}
        </span>
        <br />
        {rule.fields.map(
          (field, index) => (
            <React.Fragment key={field + index.toString()}>
              <span className="Field">{field}</span>
              <br />
            </React.Fragment>
          )
        )}
      </div>
    );
  }
}

type TextEqualsViewProps = {
  rule: Rule.Atom;
  predicate: Predicate.TextEquals;
};

function TextEqualsView({rule, predicate}: TextEqualsViewProps) {
  if (predicate.texts.length == 1) {
    return (
      <div className="AllowLineBreaks HangingIndent">
        <span className="Code">
          <span className="Field">{rule.fields[0] as string}</span>.
          <span className="Property">text</span>&nbsp;=&nbsp;
        </span>
        <span className="StringLiteral StringLiteral_InRulesTable">
          {predicate.texts[0]}
        </span>
      </div>
    );
  } else {
    return (
      <div className="AllowLineBreaks HangingIndent">
        <span className="Code">
          <span className="Field">{rule.fields[0] as string}</span>.
          <span className="Property">text</span>&nbsp;=&nbsp;
        </span>
        {predicate.texts.map((text, index) => {
          const isLast = index == predicate.texts.length - 1;
          return (
            <React.Fragment key={index.toString()}>
              <br />
              <span className="StringLiteral StringLiteral_InRulesTable">
                {text}
              </span>
              {!isLast && <span className="Code MutedText"> or</span>}
            </React.Fragment>
          );
        })}
      </div>
    );
  }
}

function showAddConstraintDialog(
  props: Props,
  modalContext: TheModalContext,
  actionContext: TheActionContext):
    void
{
  modalContext.dispatchModalAction({
    name: 'ShowModal',
    modal: <EditRuleDialog
      node={props.node}
      rule={Node.buildDefaultRule(props.node)}
      onRuleFinalized={(rule: Rule.t) =>
        actionContext.dispatchAction({
          type: 'AddRule',
          node: props.node,
          path: props.path,
          rule: rule,
        })
      }
    />,
  });
}

function reallyRunSynthesis(
  node: Node.t,
  nodePath: Model.Path,
  docName: string,
  doc: Doc.t,
  targetExtraction: Extraction.t,
  targetsSchema: TargetsSchema.t,
  blueprintSettings: Settings.BlueprintSettings,
  modalContext: TheModalContext,
  sessionContext: TheSessionContext,
  actionContext: TheActionContext):
    void
{
  modalContext.dispatchModalAction({
    name: 'ShowModal',
    modal: <AppModalBackdrop
      onCloseRequested={() => 'DontAllowClose'}
    />,
  });

  synthesis(
    doc,
    targetExtraction,
    targetsSchema,
    blueprintSettings,
    sessionContext,
  ).then(
    result => {
      // Janky.
      const newNode = {
        ...node,
        rules: result.rules, // I'm not 100% sure even that this is ok.
      };

      actionContext.dispatchAction({
        type: 'ReplaceNodeContents',
        path: nodePath,
        newNode: newNode,
      });
    }
  ).finally(
    () => {
      modalContext.dispatchModalAction({
        name: 'ReallyCloseModal',
      });
    }
  );
}

function wiifScore(
  rule: Rule.t,
  wiifNode: WiifNode.t | undefined):
    number | undefined
{
  const score =
    wiifNode &&
    WiifNode.scoreForRule(
      wiifNode, rule.uuid);

  return score;
}

function ruleScore(props: Props, rule: Rule.t): number | undefined {
  const extraction =
    props.extractions.selected;

  const ruleScore =
    extraction &&
    Scoring.ruleScore(
      extraction,
      rule.uuid);

  return ruleScore?.score;
}
