import * as Node from 'studio/blueprint/node';
import * as Rule from 'studio/blueprint/rule';
import {UUID} from 'studio/util/types';
import {v4 as uuidv4} from 'uuid';

export type t = {
  children: Node.t[];
  rules: Rule.t[];
  uuid: UUID;
  name: string | undefined;
  // weights: ...
  type: 'pick_best';
};

export function build(): t {
  return {
    children: [],
    rules: [],
    uuid: uuidv4(),
    name: undefined,
    type: 'pick_best',
  };
}
