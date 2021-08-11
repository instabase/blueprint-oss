import memo from 'memoizee';

import * as Entity from 'studio/foundation/entity';

import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';
import * as PickBestNode from 'studio/blueprint/pickBestNode';

import {isNonemptyArray, Nonempty, UUID} from 'studio/util/types';

export type t = Node.t;

export type Path = Nonempty<Node.Path>

export function build(): t {
  return PatternNode.build();
}

export function root(model: t): Node.t {
  return model;
}

export const node = memo(
  function(model: t, path: Path): Node.t | undefined {
    if (root(model).uuid != path[0]) {
      return undefined;
    } else {
      return Node.descendant(root(model), path.slice(1));
    }
  },
  { max: 30 },
);

export function hasNode(model: t, path: Path): boolean {
  return node(model, path) != undefined;
}

export function parentNode(
  model: t,
  path: Path):
    Node.WithChildren | undefined
{
  if (!hasNode(model, path)) {
    return undefined; // XXX
  } else if (path.length == 1) {
    return undefined; // XXX
  } else {
    return (node(model, (path.slice(0, -1) as Nonempty<string[]>)
                ) as Node.WithChildren | undefined);
  }
}

export function hasParent(model: t, path: Path): boolean {
  return parentNode(model, path) != undefined;
}

export function nodesAlongPath(
  model: t,
  path: Path):
    Nonempty<Node.t[]>
{
  console.assert(hasNode(model, path));
  return path.reduce((acc: Node.t[], next: UUID): Node.t[] => {
    if (acc.length == 0) {
      // assert root node UUID == next
      acc.push(root(model));
      return acc;
    } else {
      const child = Node.child(acc[acc.length - 1], next);
      // assert child
      acc.push(child as Node.t);
      return acc;
    }
  }, []) as Nonempty<Node.t[]>;
}

export function ancestors(model: t, path: Path): Node.WithChildren[] {
  return nodesAlongPath(model, path).slice(0, -1) as Node.WithChildren[];
}

export function replaceTerminusWith(
  model: t,
  path: Path,
  node: Node.t):
    t
{
  console.assert(hasNode(model, path));
  const ancestorNodes = ancestors(model, path);
  type OldUUID = UUID;
  type Acc = [Node.t, OldUUID];
  const [newRoot, _] = ancestorNodes.reduceRight((acc: Acc, next: Node.WithChildren): Acc => {
    const [newChild, oldUUID] = acc;
    return [
      Node.replaceChildWith(next, oldUUID, newChild),
      next.uuid,
    ];
  }, [node, path[path.length - 1]]);
  return newRoot;
}

export function deleteTerminus(
  model: t,
  path: Path):
    t
{
  console.assert(hasNode(model, path));
  const terminus = node(model, path) as Node.t;

  if (Node.children(terminus).length == 1) {
    return replaceTerminusWith(
      model,
      path,
      (Node.children(terminus) as any)[0]);
  } else if (path.length == 1) {
    return build();
  } else {
    const parent = parentNode(model, path) as Node.WithChildren;
    const parentPath = path.slice(0, -1) as Path;
    const newParent =
      Node.deleteChild(
        parent,
        terminus.uuid);
    return replaceTerminusWith(
      model,
      parentPath, 
      newParent);
  }
}

export function maximalValidSubpath(
  model: t,
  path: Path | undefined):
    Path | undefined
{
  if (path == undefined) {
    return undefined;
  } else if (path[0] == root(model).uuid) {
    return [path[0]].concat(
      Node.maximalValidSubpath(
        root(model),
        path.slice(1))) as Path;
  } else {
    return undefined;
  }
}

export function illegalToAddFieldNames(
  model: t,
  path: Path):
    Set<string>
{
  const result = new Set<string>();
  const incorporate = (fields: string[]) =>
    fields.forEach(field => result.add(field));

  const numNodes = path.length;

  const nodesWithUUIDs = nodesAlongPath(model, path).map(
    (node: Node.t): [Node.t, UUID] => [node, node.uuid])

  for (let i = 0; i < numNodes; ++i) {
    const [node] = nodesWithUUIDs[i];
    if (i == numNodes - 1) {
      console.assert(node.type == 'pattern');
      incorporate(Node.fields(node));
    } else if (node.type == 'merge') {
      const [_, nextUUID] = nodesWithUUIDs[i + 1];
      Node.children(node)
        .filter(child => child.uuid != nextUUID)
        .forEach(sibling => incorporate(Node.fields(sibling)));
    }
  }

  return result;
}

export function fieldType(model: t, field: string): Entity.Type | undefined {
  return Node.fieldType(model, field);
}
