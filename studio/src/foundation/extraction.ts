import memo from 'memoizee';

import * as Entity from 'studio/foundation/entity';
import * as ExtractionPoint from 'studio/foundation/extractionPoint';

export type t = {
  assignments: ExtractionPoint.t[];
};

export function build(): t {
  return {
    assignments: [],
  };
}

export const fields = memo(
  function(
    extraction: t):
      Array<string>
  {
    return extraction.assignments.map(
      ({field, entity}) => field
    );
  }
);

export const values = memo(
  function(
    extraction: t):
      Array<Entity.t>
  {
    return extraction.assignments.map(
      ({field, entity}) => entity
    );
  }
);

export const asDict = memo(
  function(extraction: t):
    Partial<Record<string, Entity.t>>
  {
    const result: Partial<Record<string, Entity.t>> = {};
    extraction.assignments.forEach(
      ({field, entity}) => {
        result[field] = entity;
      }
    );
    return result;
  }
);

export const has = memo(
  function(
    extraction: t,
    field: string):
      boolean
  {
    return value(extraction, field) != undefined;
  }
);

export const value = memo(
  function(
    extraction: t,
    field: string):
      Entity.t | undefined
  {
    return asDict(extraction)[field];
  }
);
