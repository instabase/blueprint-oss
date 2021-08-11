import React, {useState} from 'react';

// Actions
// =======

// Called to put a modal on the screen.
type ShowModal = {
  name: 'ShowModal';
  modal: JSX.Element;
};

// Can be called from anywhere to ask the current modal
// (if any) to close.
type AskModalToClose = {
  name: 'AskModalToClose';
  skipWarningIfNoModal?: boolean;
};

// Called to remove the current modal from the screen.
// Will unregister the closeRequested callback, if one is registered.
// Note that if the modal is doing any work that has
// side-effects, calling this won't (by itself) cancel that work
// (or its eventual side-effects).
type ReallyCloseModal = {
  name: 'ReallyCloseModal';
};

type CloseRequestedCB = () => 'AllowClose' | 'DontAllowClose';

// Should be called by a modal when it draws itself
// if the modal wants to intercept close attempts.
type RegisterCloseRequestedCB = {
  name: 'RegisterCloseRequestedCB';
  closeRequestedCB: CloseRequestedCB;
};

export type Action =
  | ShowModal
  | AskModalToClose
  | ReallyCloseModal
  | RegisterCloseRequestedCB
;

// Hook
// ====

export default function useModalContainer():
  [JSX.Element | undefined, (action: Action) => void]
{
  const [state, dispatch] = React.useReducer(reducer, DefaultState);
  const modal = state.name == 'ModalPresentState' ? state.modal : undefined;
  return [modal, dispatch];
}

// State
// =====

type DefaultState = {
  name: 'DefaultState';
}

type ModalPresentState = {
  name: 'ModalPresentState';
  modal: JSX.Element;
  closeRequestedCB: CloseRequestedCB | undefined;
}

type State =
  | DefaultState
  | ModalPresentState
;

const DefaultState: State = {
  name: 'DefaultState',
};

function reducer(state: State, action: Action): State {
  // console.debug('Reducing modal state', state, action);
  switch (action.name) {
    case 'ShowModal':
      if (state.name != 'DefaultState') {
        console.error('Cannot show multiple modals at once');
        return state;
      } else {
        return {
          name: 'ModalPresentState',
          modal: action.modal,
          closeRequestedCB: undefined,
        };
      }
    case 'AskModalToClose':
      if (state.name != 'ModalPresentState') {
        if (!action.skipWarningIfNoModal) {
          console.warn('Cannot ask modal to close -- no modal present!');
        }
        return state;
      } else {
        const cb = state.closeRequestedCB;
        if (cb == undefined || cb() == 'AllowClose') {
          return {name: 'DefaultState'};
        } else {
          return state;
        }
      }
    case 'ReallyCloseModal':
      if (state.name != 'ModalPresentState') {
        console.warn('Cannot close modal -- no modal present!');
        return state;
      } else {
        return {name: 'DefaultState'};
      }
    case 'RegisterCloseRequestedCB':
      if (state.name != 'ModalPresentState') {
        console.warn('Cannot register close requested CB -- no modal!');
        return state;
      } else {
        return {...state, closeRequestedCB: action.closeRequestedCB};
      }
  }
}
