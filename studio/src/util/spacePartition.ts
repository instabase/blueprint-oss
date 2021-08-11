import * as BBox from 'studio/foundation/bbox';

type BBoxGetter<U> = (u: U) => BBox.t;

export type t<U> = {
  bbox: BBox.t;
  bboxGetter: BBoxGetter<U>;
  node: Node<U>;
};

type SplitNode<U> = {
  type: 'SplitNode';
  bbox: BBox.t;
  spanningObjects: U[];
  children: Node<U>[];
};

type LeafNode<U> = {
  type: 'LeafNode';
  bbox: BBox.t;
  objects: U[];
};

type Node<U> =
  | SplitNode<U>
  | LeafNode<U>
;

const MAX_NUM_OBJECTS_WITHOUT_SPLIT = 5;

export function build<U>(bbox: BBox.t, bboxGetter: BBoxGetter<U>): t<U> {
  return {
    bbox,
    bboxGetter,
    node: buildLeafNode(bbox),
  };
}

export function add<U>(spacePartition: t<U>, u: U): t<U> {
  return {
    ...spacePartition,
    node: addPrivate(spacePartition.node, u, spacePartition.bboxGetter),
  };
}

export function getIntersecting<U>(spacePartition: t<U>, bbox: BBox.t): U[] {
  return getIntersectingPrivate(
    spacePartition.node,
    bbox,
    spacePartition.bboxGetter,
  );
}

function buildSplitNode<U>(bbox: BBox.t): SplitNode<U> {
  const childBBoxes = BBox.splitSquareLike(bbox);

  return {
    type: 'SplitNode',
    bbox,
    spanningObjects: [],
    children: childBBoxes.map(childBBox => buildLeafNode<U>(childBBox)),
  };
}

function buildLeafNode<U>(bbox: BBox.t): LeafNode<U> {
  return {
    type: 'LeafNode',
    bbox: bbox,
    objects: [],
  };
}

function addPrivate<U>(node: Node<U>, u: U, bboxGetter: BBoxGetter<U>): Node<U> {
  switch(node.type) {
    case 'LeafNode':
      if (node.objects.length >= MAX_NUM_OBJECTS_WITHOUT_SPLIT) {
        let splitNode: Node<U> = buildSplitNode(node.bbox);
        node.objects.forEach(
          object => splitNode = addPrivate(splitNode, object, bboxGetter)
        );
        return addPrivate(splitNode, u, bboxGetter);
      } else {
        return {
          ...node,
          objects: node.objects.concat([u]),
        };
      }
    case 'SplitNode':
      function contains(child: Node<U>): boolean {
        return BBox.contains(child.bbox, bboxGetter(u));
      }

      const childrenContainingEntry = node.children.filter(contains);

      if (childrenContainingEntry.length == 0) {
        return {
          ...node,
          spanningObjects: node.spanningObjects.concat([u]),
        };
      } else if (childrenContainingEntry.length == 1) {
        return {
          ...node,
          children: node.children.map(
            child => {
              if (child == childrenContainingEntry[0]) {
                return addPrivate(child, u, bboxGetter);
              } else {
                return child;
              }
            }
          ),
        };
      } else {
        throw 'Multiple children should not contain your entry';
      }
  }
}

function getIntersectingPrivate<U>(
  node: Node<U>,
  bbox: BBox.t,
  bboxGetter: BBoxGetter<U>):
    U[]
{
  if (!BBox.intersect(node.bbox, bbox)) {
    return [];
  } else {
    function intersect(u: U): boolean {
      return BBox.intersect(bbox, bboxGetter(u));
    }

    switch(node.type) {
      case 'LeafNode':
        return node.objects.filter(intersect);
      case 'SplitNode':
        return [
          ...node.children.map(
            child => getIntersectingPrivate(child, bbox, bboxGetter)
          ).flat(),
          ...node.spanningObjects.filter(intersect),
        ];
    }
  }
}
