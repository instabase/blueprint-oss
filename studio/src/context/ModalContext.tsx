import React from 'react';
import {Action as ModalAction} from 'studio/hooks/useModalContainer';

export type Value = {
  dispatchModalAction: (action: ModalAction) => void;
  currentModal: JSX.Element | undefined;
  higherModalContext?: Value;
};

function warning() {
  console.warn('Using empty app context');
}

const Default = {
  dispatchModalAction: warning,
  currentModal: undefined,
};

export default React.createContext<Value>(Default);

export function modalOpen(context: Value | undefined): boolean {
  while (context) {
    if (context.currentModal != undefined) {
      return true;
    } else {
      context = context.higherModalContext;
    }
  }
  return false;
}
