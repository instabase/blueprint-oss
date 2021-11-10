import React from 'react';
import * as Handle from 'studio/state/handle';
import assert from 'studio/util/assert';

export type Value = {
  uuid: string;
  backendURL: string;
  handle: Handle.t | undefined;
  setHandle: (handle: Handle.t | undefined) => void;
};

export const Default = {
  type: undefined as any,
  uuid: undefined as any,
  backendURL: undefined as any,
  handle: undefined as any,
  setHandle: undefined as any,
};

export default React.createContext<Value>(Default);
