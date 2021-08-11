import React from 'react';
import * as State from 'studio/state/dragSelection';

export type Value<T> = {
  register: (element: HTMLDivElement, t: T, setState: State.Setter) => void;
  unregister: (element: HTMLDivElement) => void;
};

export function isCorrectlyTyped<T>(v: Value<any>): v is Value<T> {
  return true; // Hmm.
}

export default React.createContext<Value<any> | undefined>(undefined);
