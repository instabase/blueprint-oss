import React from 'react';
import * as ServerInfo from 'studio/state/serverInfo';
import assert from 'studio/util/assert';

export type Value = {
  uuid: string;
  backendURL: string;
  serverInfo: ServerInfo.t | undefined;
  projectPath: string | undefined;
  setProjectPath: (path: string | undefined) => void;
};

const warning = () => console.warn('Using empty session context');

export const Default = {
  type: undefined as any,
  uuid: undefined as any,
  backendURL: undefined as any,
  serverInfo: undefined as any,
  projectPath: undefined as any,
  setProjectPath: undefined as any,
};

export default React.createContext<Value>(Default);
