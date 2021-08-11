import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Entity from 'studio/foundation/entity';
import * as Rule from 'studio/blueprint/rule';

import {UUID} from 'studio/util/types';

export type t = {
  fields: Partial<Record<string, Entity.Type>>;
  // allowed_to_overlap: ...
  rules: Rule.t[];
  uuid: UUID;
  name: string | undefined;
  type: 'pattern';
};

export function fields(node: t): string[] {
  return [...Object.keys(node.fields)];
}

export function hasField(node: t, field: string): boolean {
  return fields(node).find(f => f == field) != undefined;
}

// This includes subrules of connectives.
export const allRules = memo(
  function(node: t):
    Set<Rule.t>
  {
    const result = new Set<Rule.t>();
    function handle(rule: Rule.t) {
      result.add(rule);
      if (rule.type != 'atom') {
        rule.rules.forEach(handle);
      }
    }
    node.rules.forEach(handle);
    return result;
  },
  { max: 10 },
);

export function hasRule(node: t, rule: Rule.t): boolean {
  return allRules(node).has(rule);
}

export function build(): t {
  return {
    fields: {},
    rules: [],
    uuid: uuidv4(),
    name: undefined,
    type: 'pattern',
  };
}

export function copy(node: t): t {
  return {
    ...node,
    name: copyName(node.name),
    uuid: uuidv4(),
  };
}

function copyName(
  original: string | undefined):
    string | undefined
{
  if (original == undefined) {
    return undefined;
  } else if (original.startsWith('Copy of ')) {
    return original;
  } else {
    return 'Copy of ' + original;
  }
}

export function fieldType(
  node: t,
  field: string):
    Entity.Type | undefined
{
  return node.fields[field];
}
