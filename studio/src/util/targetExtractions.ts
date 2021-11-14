import memo from 'memoizee';

import * as DocTargets from 'studio/foundation/docTargets';
import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';
import * as ExtractionPoint from 'studio/foundation/extractionPoint';
import * as Doc from 'studio/foundation/doc';
import * as TargetValue from 'studio/foundation/targetValue';
import * as TargetsSchema from 'studio/foundation/targetsSchema';

import * as Node from 'studio/blueprint/node';
import * as PatternNode from 'studio/blueprint/patternNode';

import * as SpacePartition from 'studio/util/spacePartition';

import makeDocSpacePartition from 'studio/util/makeDocSpacePartition';

import assert from 'studio/util/assert';

export const build = memo(
  function(
    doc: Doc.t,
    docTargets: DocTargets.t,
    targetsSchema: TargetsSchema.t):
      Extraction.t
  {
    const assignments: ExtractionPoint.t[] = [];
    for (let {field, value} of docTargets.assignments) {
      if (TargetValue.isPositioned(value)) {
        const percentageBBox = TargetValue.bbox(value);
        const bbox = Doc.absoluteBBox(doc, percentageBBox);

        const type = TargetsSchema.type(targetsSchema, field);

        if (type == undefined) {
          throw `Target field ${field} not present in target schema`;
        }

        const partition = makeDocSpacePartition(doc, type);

        for (let entity of SpacePartition.getIntersecting(partition, bbox)) {
          if (Entity.text(entity) == value.text) {
            assignments.push({field, entity});
            break;
          }
        }
      }
    }
    return {assignments};
  },
  { max: 10 },
);

export const buildComplete = memo(
  function(
    doc: Doc.t,
    node: PatternNode.t,
    docTargets: DocTargets.t,
    targetsSchema: TargetsSchema.t):
      Extraction.t | undefined
  {
    const extraction = build(doc, docTargets, targetsSchema);
    if (isComplete(extraction, node, docTargets)) {
      return extraction;
    }
  },
  { max: 10 },
);

function isComplete(
  extraction: Extraction.t,
  node: PatternNode.t,
  docTargets: DocTargets.t):
    boolean
{
  // If any of this node's fields has a target value which is null or undefined,
  // we say that there are by definition no complete target extractions for this
  // doc / node / targets combination.
  
  // Returns true if the extraction has a correctly-typed entity
  // for every target value, and each of the node's fields has a target value.
  
  for (let field of Node.fields(node)) {
    if (!DocTargets.hasPositionedValue(docTargets, field)) {
      return false;
    } else if (!Extraction.has(extraction, field)) {
      return false;
    } else {
      const typeFromNode = PatternNode.fieldType(node, field);
      const typeFromExtraction = Extraction.value(extraction, field)?.type;

      if (typeFromNode != typeFromExtraction) {
        return false;
      }
    }
  }

  // We're allowing (in principle) the extraction having extra fields
  // which are not in the targets.

  return true;
}
