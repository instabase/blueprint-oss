import React from 'react';

import ModalContext from 'studio/context/ModalContext';

import * as Node from 'studio/blueprint/node';
import * as Predicate from 'studio/blueprint/predicate';
import * as Rule from 'studio/blueprint/rule';

import * as PseudoAtom from 'studio/state/pseudoAtom';

import {Plus, Trash2} from 'studio/components/StockSVGs';
import Dialog from 'studio/components/./Dialog';
import AppModalBackdrop from 'studio/components/AppModalBackdrop';
import Dropdown from 'studio/components/./Dropdown';
import './EditRuleDialog.css';
import {v4 as uuidv4} from 'uuid';

type Props = {
  node: Node.t;
  rule: Rule.t;
  onRuleFinalized: (rule: Rule.t) => void;
};

export default function EditRuleDialog(props: Props) {
  const modalContext = React.useContext(ModalContext);

  const [rule, setRule] =
    React.useState<PseudoAtom.t>(
      PseudoAtom.fromRule(
        props.rule) as PseudoAtom.t);
  const defaultField = Node.fields(props.node)[0];
  const predicate = rule.predicate;

  const close = () => modalContext.dispatchModalAction({name: 'AskModalToClose'});

  return <AppModalBackdrop>
    <Dialog>
      <div className="EditRuleDialog">
        <div>Constraint</div>
        <Dropdown<Predicate.Name>
          options={Predicate.Names}
          selected={predicate.name}
          stringify={(name: Predicate.Name) => name}
          onSelected={(name: Predicate.Name) => {
            if (name != predicate.name) {
              const predicate = Predicate.build(name);
              const newRule = {...rule, predicate};

              const maxNumFields = PseudoAtom.maxNumFields(predicate);
              if (maxNumFields != undefined) {
                while (newRule.fields.length > maxNumFields) {
                  newRule.fields.splice(-1, 1);
                }
              }

              while (newRule.fields.length < PseudoAtom.minNumFields(newRule.predicate)) {
                newRule.fields.push(defaultField);
              }

              setRule(newRule);
            }
          }}
        />
        <div/>
        <div/>

        {predicate.name == 'text_equals' && predicate.texts.map((text, index) => {
          const isFirst = index == 0;
          const isLast = index == predicate.texts.length - 1;

          return (
            <React.Fragment key={index.toString()}>
              {isFirst && <div>Text</div>}
              {!isFirst &&
                <div
                  style={{
                    textAlign: 'right'
                  }}
                  className="MutedText"
                >
                or
                </div>
              }

              <input
                type="text"
                value={text}
                onChange={
                  event => {
                    const texts = [...predicate.texts];
                    texts[index] = event.target.value;
                    setRule({
                      ...rule,
                      predicate: {
                        ...predicate,
                        texts,
                      }
                    });
                  }
                }
                onClick={
                  event => event.stopPropagation()
                }
              />
              <div>
                <button
                  className="SVGButton"
                  onClick={event => {
                    event.stopPropagation();
                    event.preventDefault();
                    const texts = [...predicate.texts];
                    texts.splice(index, 1);
                    setRule({
                      ...rule,
                      predicate: {...predicate, texts}
                    });
                  }}
                  disabled={isFirst && isLast}
                >
                  <Trash2 />
                </button>
              </div>
              <div>
                {isLast &&
                  <button
                    className="SVGButton"
                    onClick={event => {
                      event.stopPropagation();
                      event.preventDefault();
                      const texts = [...predicate.texts, ''];
                      setRule({
                        ...rule,
                        predicate: {...predicate, texts}
                      });
                    }}
                  >
                    <Plus />
                  </button>
                }
              </div>
            </React.Fragment>
          );
        })}

        {rule.fields.map((field, index) => (
          <React.Fragment key={field + index.toString()}>
            <div>
              {index == 0 &&
                `Field${rule.fields.length > 1 ? 's' : ''}`
              }
            </div>

            <Dropdown
              options={Node.fields(props.node)}
              selected={field}
              stringify={(f: string) => f}
              onSelected={newField =>
                setRule(PseudoAtom.withIthField(rule, index, newField))}
            />

            <div>
              <button
                className="SVGButton"
                onClick={event => {
                  event.stopPropagation();
                  event.preventDefault();
                  setRule(PseudoAtom.withIthFieldDeleted(rule, index));
                }}
                disabled={rule.fields.length - 1 < PseudoAtom.minNumFields(rule.predicate)}
              >
                <Trash2 />
              </button>
            </div>

            <div />
          </React.Fragment>
        ))}

        {'tolerance' in predicate && <React.Fragment>
          <div>Tolerance</div>
          <input 
            type="number"
            value={predicate.tolerance}
            min="0"
            onChange={
              event => {
                const tolerance = parseFloat(event.target.value);
                setRule({
                  ...rule,
                  predicate: {
                    ...predicate,
                    tolerance,
                  },
                });
              }
            }
            onClick={
              event => event.stopPropagation()
            }
          />
          <div/>
          <div/>
        </React.Fragment>
        }

        {'maximum_impingement' in predicate && <React.Fragment>
          <div>Maximum Impingement</div>
          <input 
            type="number"
            value={predicate.maximum_impingement}
            min="0"
            onChange={
              event => {
                const maximum_impingement = parseFloat(event.target.value);
                setRule({
                  ...rule,
                  predicate: {
                    ...predicate,
                    maximum_impingement,
                  },
                });
              }
            }
            onClick={
              event => event.stopPropagation()
            }
          />
          <div/>
          <div/>
        </React.Fragment>
        }

        {'taper' in predicate && <React.Fragment>
          <div>Taper</div>
          <input 
            type="number"
            value={predicate.taper}
            min="0"
            onChange={
              event => {
                const taper = parseFloat(event.target.value);
                setRule({
                  ...rule,
                  predicate: {
                    ...predicate,
                    taper,
                  },
                });
              }
            }
            onClick={
              event => event.stopPropagation()
            }
          />
        </React.Fragment>
        }
      </div>

      <div className="DialogButtons">
        <button onClick={event => {
          event.stopPropagation();
          event.preventDefault();
          close();
        }}>
          Cancel
        </button>
        <button
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              setRule({
                ...rule,
                fields: rule.fields.concat([defaultField]),
              });
            }
          }
          disabled={PseudoAtom.maxNumFields(rule.predicate) != undefined &&
                    rule.fields.length + 1 > (PseudoAtom.maxNumFields(rule.predicate) as number)}
        >
          Add field
        </button>
        <button autoFocus onClick={
          event => {
            event.stopPropagation();
            event.preventDefault();
            const finalRule = PseudoAtom.toRule(rule);
            if (finalRule) {
              props.onRuleFinalized(finalRule);
            }
            close();
          }
        }>
          Ok
        </button>
      </div>
    </Dialog>
  </AppModalBackdrop>;
}
