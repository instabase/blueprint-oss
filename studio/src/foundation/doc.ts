import memo from 'memoizee';

import * as BBox from 'studio/foundation/bbox';
import * as Entity from 'studio/foundation/entity';

export type t = {
  bbox: BBox.t;
  entities: Entity.t[];
  name: string | undefined;
};

export const typeNames = memo(
  function(doc: t): string[] {
    const set = new Set<string>(
      [...doc.entities.map(entity => entity.type)]
    );

    return [...set].sort();
  }
);

// It is guaranteed that the indices of entities are stable.
export const entitiesHavingType = memo(
  function<ConcreteEntitySubclass extends Entity.t>(
    doc: t,
    typeName: ConcreteEntitySubclass['type']):
      ConcreteEntitySubclass[]
  {
    function isCorrectlyTyped(e: Entity.t): e is ConcreteEntitySubclass {
      return e.type == typeName;
    }

    return doc.entities.filter(isCorrectlyTyped);
  }
);

export const getWords = memo(
  function(doc: t): Entity.t[] {
    return doc.entities.filter(entity =>
      entity.type == 'Text' && entity.words.length == 1);
  }
);

export function absoluteBBox(doc: t, percentageBBox: BBox.t): BBox.t {
  return BBox.absolutePositionIn(doc.bbox, percentageBBox);
}

export function percentageBasedPositionIn(doc: t, bbox: BBox.t): BBox.t {
  return BBox.percentageBasedPositionIn(bbox, doc.bbox);
}
