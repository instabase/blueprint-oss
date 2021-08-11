import React from 'react';
import * as Project from 'studio/state/project';

export type Value = {
  project: Project.t | undefined;
};

const Default = {
  project: undefined,
};

export default React.createContext<Value>(Default);;
