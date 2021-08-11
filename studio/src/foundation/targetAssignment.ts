import memo from 'memoizee';

import * as TargetValue from 'studio/foundation/targetValue';

export type t = {
  field: string;
  value: TargetValue.t;
};

export const asDict = memo(
  function(assignments: t[]):
    Partial<Record<string, TargetValue.t>>
  {
    const result: Partial<Record<string, TargetValue.t>> = {};
    assignments.forEach(
      ({field, value}) => result[field] = value
    );
    return result;
  }
);

export function merged(existing: t[], provided: t[]): t[] {
  const existingFields = new Set(existing.map(a => a.field));
  const providedValues = asDict(provided);
  return [
    ...existing.map(
      ({field, value}) => ({
        field,
        value:
          TargetValue.merged(
            value,
            providedValues[field]),
      })
    ),
    ...provided.filter(
      ({field}) => !existingFields.has(field)
    ),
  ];
}
