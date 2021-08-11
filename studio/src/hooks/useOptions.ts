import React from 'react';
import useLocalStorageState from 'studio/hooks/useLocalStorageState';
import {isObject, isBoolean} from 'studio/util/types';

export type Values = Record<string, boolean>;

export type Option = {
  checked: boolean;
  setChecked: (newValue: boolean) => void;
};

export type Options = Record<string, Option>;

export default function useOptions(
  localStorageKey: string,
  defaults: Values):
    Options
{
  const [laggingInternalValues, setLaggingInternalValues] =
    useLocalStorageState<Values>(
      localStorageKey,
      EmptyValues,
      validator);

  let internalValues = laggingInternalValues;
  const setInternalValues = (newValues: Values) => {
    internalValues = newValues;
    setLaggingInternalValues(newValues);
  };

  React.useEffect(() => {
    setInternalValues(
      foldInValuesNotPresent(
        internalValues,
        defaults));
  }, [localStorageKey, defaults]);

  const result: Options = {};
  Object.keys(defaults).forEach(k => {
    if (k in internalValues) {
      result[k] = {
        checked: internalValues[k],
        setChecked: (newValue: boolean) => {
          setInternalValues({
            ...internalValues,
            [k]: newValue,
          });
        },
      };
    }
  });
  return result;
}

function validator(x: unknown): x is Values {
  return isObject(x) &&
         Object.values(x).every(v => isBoolean(v));
}

function foldInValuesNotPresent(initial: Values, toAdd: Values): Values {
  const result = {...initial};
  Object.keys(toAdd).forEach(k => {
    if (!(k in result)) {
      result[k] = toAdd[k];
    }
  });
  return result;
}

const EmptyValues = {};
