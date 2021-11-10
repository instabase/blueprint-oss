import memo from 'memoizee';

import * as Entity from 'studio/foundation/entity';
import * as Doc from 'studio/foundation/doc';

import * as SpacePartition from 'studio/util/spacePartition';

export default memo(
  function<ConcreteEntitySubclass extends Entity.t>(
    doc: Doc.t,
    type: ConcreteEntitySubclass['type'],
    filter?: (entity: Entity.t) => boolean):
      SpacePartition.t<ConcreteEntitySubclass>
  {
    let result = SpacePartition.build(
      doc.bbox,
      (e: ConcreteEntitySubclass) => e.bbox,
    );

    Doc.entitiesHavingType(doc, type).forEach(
      entity => {
        if (filter == undefined || filter(entity)) {
          result = SpacePartition.add(result, entity);
        }
      }
    );

    return result;
  },
  { max: 70 },
);
