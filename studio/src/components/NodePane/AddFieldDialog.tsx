import React from 'react';

import ModalContext from 'studio/context/ModalContext';
import ActionContext from 'studio/context/ActionContext';
import {Value as TheActionContext} from 'studio/context/ActionContext';

import Checkbox from 'studio/components/Checkbox';
import Dialog from 'studio/components/Dialog';
import AppModalBackdrop from 'studio/components/AppModalBackdrop';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';

import * as Entity from 'studio/foundation/entity';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import useLocalStorageState from 'studio/hooks/useLocalStorageState';

import './AddFieldDialog.css';

import {isObject, hasOwnProperty} from 'studio/util/types';

type Props = {
  model: Model.t;
  node: PatternNode.t;
  path: Model.Path;
  fields: Partial<Record<string, Entity.Type>>;
  annotationMode: boolean;
};

export default function AddFieldDialog(props: Props) {
  const modalContext = React.useContext(ModalContext);
  const actionContext = React.useContext(ActionContext);

  const fields = Object.keys(props.fields);
  const illegalFields =
    React.useMemo(() =>
      Model.illegalToAddFieldNames(
        props.model, props.path),
      [props.model, props.path])
  const legalFields =
    fields.filter(field => !illegalFields.has(field));

  const defaultMemoDict = React.useMemo(() => {
    const result: MemoDict_XXX = {};
    legalFields.forEach(field => result[field] = {toBeAdded: true});
    return result;
  }, []);

  const [memo, setMemo] =
    useLocalStorageState<MemoDict_XXX>(
      'Studio.AddFieldDialog.MemoDict-v2',
      defaultMemoDict,
      isMemoDict_XXX);

  const toBeAdded = (field: string) => (
    !illegalFields.has(field) && memo[field] && memo[field].toBeAdded
  );

  const showAsChecked = (field: string) => (
    toBeAdded(field) || Node.hasField(props.node, field)
  );

  const setToBeAdded = (fields: string[], value: boolean) => {
    // This is so lame. If setToBeAdded only accepted one field, you couldn't call it multiple times
    // within the same event frame because the local memo var doesn't get updated synchronously.
    const newMemo = {...memo};
    fields.forEach(field => newMemo[field] = {toBeAdded: value});
    setMemo(newMemo);
  };

  const fieldsToAdd = fields.filter(toBeAdded);

  const allLegalFieldsToBeAdded =
    legalFields.every(field => toBeAdded(field));

  const [mainBodyHidden, setMainBodyHidden] =
    React.useState<boolean>(
      props.annotationMode
    );

  const close = () => {
    modalContext.dispatchModalAction({name: 'AskModalToClose'});
  };

  const finalizeAddFields = (fields: string[] | undefined): void => {
    const type = (field: string): Entity.Type => (
      props.fields[field] || Entity.DefaultType
    );

    if (fields != undefined) {
      actionContext.dispatchAction({
        type: 'AddFields',
        node: props.node,
        path: props.path,
        fields: fields.map(field => [field, type(field)]),
      });
    }

    close();
  };

  const toggleAll = React.useCallback(() => {
    if (!allLegalFieldsToBeAdded) {
      setToBeAdded(legalFields, true);
    } else {
      setToBeAdded(legalFields, false);
    }
  }, [allLegalFieldsToBeAdded, legalFields]);

  const goIntoCustomDialogFlow = () => {
    setTimeout(() => {
      const field: string | undefined =
        showAddCustomFieldDialog(props.node);
      if (field == undefined) {
        if (props.annotationMode) {
          close();
        } else {
          setMainBodyHidden(false);
        }
      } else if (illegalFields.has(field)) {
        alert('Cannot use that field name. ' +
              'Either a field by that name already exists in this pattern, ' +
              'or a field by this name exists in a pattern which could ' +
              'be merged with this one elsewhere in the model.');
        close();
      } else {
        finalizeAddFields([field]);
      };
    }, 100);
  };

  React.useEffect(() => {
    if (props.annotationMode) {
      goIntoCustomDialogFlow();
    }
  }, []);

  return <AppModalBackdrop>
    {!mainBodyHidden && <Dialog>
      <div className="AddFieldDialog">
        <div className="_description">
          Add fields
        </div>

        {fields.map(field =>
          <Row
            key={field}
            field={field}
            disabled={illegalFields.has(field)}
            showAsChecked={showAsChecked(field)}
            setToBeAdded={(value) => {setToBeAdded([field], value)}}
          />
        )}

        <Checkbox
          checked={legalFields.length > 0 && allLegalFieldsToBeAdded}
          disabled={legalFields.length == 0}
          setChecked={toggleAll}
        />
        <div
          className="SmallText MutedText DisallowUserSelection"
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              toggleAll();
            }
          }
        >
          (Toggle all)
        </div>
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
          autoFocus
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();

              setMainBodyHidden(true);
              goIntoCustomDialogFlow();
            }
          }
        >
          Custom…
        </button>
        <button
          disabled={fieldsToAdd.length == 0}
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              finalizeAddFields(fieldsToAdd);
            }
          }
        >
          Ok
        </button>
      </div>
    </Dialog>}
  </AppModalBackdrop>;
}

type RowProps = {
  field: string;
  showAsChecked: boolean;
  disabled: boolean;
  setToBeAdded: (newValue: boolean) => void;
};

function Row(props: RowProps) {
  return <>
    <Checkbox
      checked={props.showAsChecked}
      disabled={props.disabled}
      setChecked={props.setToBeAdded}
    />
    <div
      className={
        'Field DisallowUserSelection' +
        (props.disabled ? ' VeryMutedText' : '')
      }
      onClick={
        event => {
          event.stopPropagation();
          event.preventDefault();
          if (!props.disabled) {
            props.setToBeAdded(!props.showAsChecked);
          }
        }
      }
    >
      {props.field}
    </div>
  </>;
}

type MemoDict_XXX = {
  [field: string]: {
    toBeAdded: boolean;
  };
};

function isMemoDict_XXX(o: unknown): o is MemoDict_XXX {
  return isObject(o); /* && Object.entries(o).every(
    ([key, value]) => {
      return hasOwnProperty(value, 'toBeAdded') && isBoolean(value.toBeAdded) &&
             hasOwnProperty(value, 'label') && isBoolean(value.label);
    }); */
}

function showAddCustomFieldDialog(node: PatternNode.t): string | undefined {
  const field = prompt('New field', 'net_pay');
  if (!field) {
    return undefined;
  } else if (Node.fields(node).indexOf(field) != -1) {
    const error = `Field ${field} already exists`;
    alert(error);
  } else {
    return field;
  }
}
