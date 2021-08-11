import React from 'react';
import {Action} from 'studio/state/mainReducer';

export type Value = {
  dispatchAction: (action: Action) => void,
};

const Default = {
  dispatchAction: (_: any) => {
    console.warn('Using empty action context');
  },
};

export default React.createContext<Value>(Default);;
