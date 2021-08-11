import * as Node from 'studio/blueprint/node';
import * as Rule from 'studio/blueprint/rule';
import {UUID} from 'studio/util/types';

export type t = {
  children: Node.t[];
  dependency_graph: undefined;
  rules: Rule.t[];
  uuid: UUID;
  name: string | undefined;
  // weights: ...
  type: 'merge';
};
