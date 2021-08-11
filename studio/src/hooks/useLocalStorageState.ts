import React from 'react';
import {saveToLocalStorage, loadFromLocalStorage} from 'studio/util/localStorage';
import depsOk from 'studio/util/depsOk';
import useTriggerUpdate from 'studio/hooks/useTriggerUpdate';

export default function useLocalStorageState<T>(
  localStorageKey: string,
  defaultValue: T,
  validator: (t: unknown) => t is T):
    [T, (t: T) => void]
{
  const triggerUpdate = useTriggerUpdate();

  const deps = [localStorageKey, defaultValue, validator];

  type SavedValueWithDeps = {
    value: T;
    deps: unknown[];
  };

  const initialValueAndDeps = () => ({
    value:
      loadFromLocalStorage(
        localStorageKey,
        defaultValue,
        validator
      ),
    deps,
  });

  const savedValueRef =
    React.useRef<SavedValueWithDeps>(
      initialValueAndDeps());

  if (!depsOk(savedValueRef.current.deps, deps)) {
    savedValueRef.current = initialValueAndDeps();
  }

  const setValue = React.useCallback(
    (value: T) => {
      saveToLocalStorage(localStorageKey, value);
      savedValueRef.current = {value, deps};
      triggerUpdate();
    },
    deps,
  );

  return [savedValueRef.current.value, setValue];
}
