import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Entity from 'studio/foundation/entity';

import * as MergeNode from 'studio/blueprint/mergeNode';
import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as PickBestNode from 'studio/blueprint/pickBestNode';
import * as Predicate from 'studio/blueprint/predicate';
import * as Rule from 'studio/blueprint/rule';

import assert from 'studio/util/assert';
import {hasOwnProperty, UUID, Nonempty} from 'studio/util/types';

export type Path = UUID[];

export type WithChildren =
  | PickBestNode.t
  | MergeNode.t
;

export type t =
  | PatternNode.t
  | PickBestNode.t
  | MergeNode.t
;

export type Type = t['type'];

export function displayName(node: t): string {
  if (node.name != undefined) {
    return node.name;
  } else {
    switch (node.type) {
      case 'pattern':
        return 'Pattern';
      case 'pick_best':
        return 'Pick best';
      case 'merge':
        return 'Merge';
    }
  }
}

export function children(node: t): t[] {
  return (hasOwnProperty(node, 'children') && Array.isArray(node.children))
    ? node.children : [];
}

export function hasChildren(node: t): boolean {
  return children(node).length > 0;
}

export function descendant(node: t, path: UUID[]): t | undefined {
  if (path.length == 0) {
    return node;
  } else {
    const next = child(node, path[0]);
    if (next) {
      return descendant(next, path.slice(1));
    } else {
      return undefined;
    }
  }
}

export function hasDescendant(node: t, path: Path): boolean {
  return descendant(node, path) != undefined;
}

export function child(node: t, childID: UUID): t | undefined {
  return children(node).find(child => child.uuid == childID);
}

export function hasChild(node: t, childID: UUID): boolean {
  return child(node, childID) != undefined;
}

export function replaceChildWith(
  node: WithChildren,
  childID: UUID,
  replacement: t):
    WithChildren
{
  const newChildren = [...children(node)];
  const index = newChildren.findIndex(child => child.uuid == childID);
  // assert index != -1
  newChildren[index] = replacement;
  return {...node, children: newChildren};
}

export function deleteChild(
  node: WithChildren,
  childID: UUID):
    WithChildren
{
  console.assert(hasChild(node, childID));
  return {...node, children: node.children.filter(child => child.uuid != childID)};
}

export function validDepth(node: t, path: Path): number {
  if (path.length == 0) {
    return 0;
  } else {
    const next = child(node, path[0]);
    if (next) {
      return 1 + validDepth(next, path.slice(1));
    } else {
      return 0;
    }
  }
}

export function maximalValidSubpath(node: t, path: Path): Path {
  return path.slice(0, validDepth(node, path));
}

export function hasField(node: t, field: string): boolean {
  if (node.type == 'pattern') {
    return PatternNode.hasField(node, field);
  } else {
    return children(node).some(child => hasField(child, field));
  }
}

export function hasRule(node: t, rule: Rule.t): boolean {
  if (node.type == 'pattern') {
    return PatternNode.hasRule(node, rule);
  } else {
    return children(node).some(child => hasRule(child, rule));
  }
}

export const fields = memo(
  function(node: t): string[] {
    if (node.type == 'pattern') {
      return [...Object.keys(node.fields)];
    } else {
      const accountedFor = new Set<string>();
      const result: string[] = [];
      children(node).forEach(child => {
        fields(child).forEach(field => {
          if (!accountedFor.has(field)) {
            accountedFor.add(field);
            result.push(field);
          }
        });
      });
      return result;
    }
  },
  { max: 150 },
);

export function rules(node: t): Rule.t[] {
  return node.rules;
}

export function rule(node: t, ruleUUID: UUID): Rule.t | undefined {
  return Rule.asDict(node.rules)[ruleUUID];
}

export function numRules(node: t): number {
  return rules(node).length;
}

export function numFields(node: t): number {
  return fields(node).length;
}

export function canHaveChildren(node: t): boolean {
  return node.type == 'merge' || node.type == 'pick_best';
}

export function buildDefaultRule(node: t): Rule.t {
  console.assert(Node.fields(node).length > 0);
  return {
    type: 'atom',
    name: undefined,
    uuid: uuidv4(),
    fields: Node.fields(node).slice(0, 1),
    predicate: Predicate.build('text_equals'),
  };
}

export function fieldType(node: t, field: string): Entity.Type | undefined {
  if (node.type == 'pattern') {
    return node.fields[field];
  } else {
    for (let child of children(node)) {
      if (hasField(child, field)) {
        return fieldType(child, field);
      }
    }
  }
}

type FieldTypePair = [string, Entity.Type];

export function fieldTypePairs(node: t): FieldTypePair[] {
  return fields(node).map(
    field => {
      const type = fieldType(node, field);
      if (type == undefined) {
        throw 'Node somehow has field of unknown type';
      }
      return [field, type];
    }
  );
}
