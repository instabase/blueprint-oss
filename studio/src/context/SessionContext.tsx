import React from 'react';
import assert from 'studio/util/assert';

export type Value = {
  uuid: string;
  backendURL: string;
  projectPath: string | undefined;
  setProjectPath: (path: string | undefined) => void;
};

const warning = () => console.warn('Using empty session context');

export const Default = {
  type: undefined as any,
  uuid: undefined as any,
  backendURL: undefined as any,
  projectPath: undefined as any,
  setProjectPath: undefined as any,
};

export default React.createContext<Value>(Default);
