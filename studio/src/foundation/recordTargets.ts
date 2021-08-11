import memo from 'memoizee';

import * as TargetAssignment from 'studio/foundation/targetAssignment';
import * as TargetValue from 'studio/foundation/targetValue';

import assert from 'studio/util/assert';

export type t = {
  doc_name: string;
  assignments: TargetAssignment.t[];
  doc_tags: string[];
  notes: string | undefined;
};

export function build(recordName: string): t {
  return {
    doc_name: recordName,
    assignments: [],
    doc_tags: [],
    notes: undefined,
  };
}

export function isEmpty(recordTargets: t): boolean {
  return fields(recordTargets).length == 0;
}

export const fields = memo(
  function(recordTargets: t): string[] {
    return recordTargets.assignments.map(
      ({field, value}) => field
    );
  }
);

export function hasValue(recordTargets: t, field: string): boolean {
  return asDict(recordTargets)[field] != undefined;
}

export function hasAllValues(recordTargets: t, fields: string[]): boolean {
  return fields.every(field => hasValue(recordTargets, field));
}

export function hasNonNullValue(recordTargets: t, field: string): boolean {
  const value = asDict(recordTargets)[field];
  return value != undefined && TargetValue.isNonNull(value);
}

export function hasAllNonNullValues(recordTargets: t, fields: string[]): boolean {
  return fields.every(field => hasNonNullValue(recordTargets, field));
}

export function hasPositionedValue(recordTargets: t, field: string): boolean {
  const value = asDict(recordTargets)[field];
  return value != undefined && TargetValue.isPositioned(value);
}

export function hasAllPositionedValues(recordTargets: t, fields: string[]): boolean {
  return fields.every(field => hasPositionedValue(recordTargets, field));
}

export const asDict = memo(
  function(
    recordTargets: t):
      Partial<Record<string, TargetValue.t>>
  {
    const result: Partial<Record<string, TargetValue.t>> = {};
    recordTargets.assignments.forEach(
      ({field, value}) => result[field] = value
    );
    return result;
  }
);

export const asRecordNameDict = memo(
  function(recordTargets: t[]):
    Partial<Record<string, t>>
  {
    const result: Partial<Record<string, t>> = {};
    recordTargets.forEach(
      forDoc => {
        result[forDoc.doc_name] = forDoc;
      }
    );
    return result;
  }
);

export const value = memo(
  function(
    recordTargets: t,
    field: string):
      TargetValue.t | undefined
  {
    return asDict(recordTargets)[field];
  }
);

export function merged(existing: t[], provided: t[]): t[] {
  const existingDict = asRecordNameDict(existing);
  const providedDict = asRecordNameDict(provided);
  const recordNames = new Set([...Object.keys(existingDict),
                            ...Object.keys(providedDict)]);
  return [...recordNames].map(
    recordName => mergedForDoc(existingDict[recordName], providedDict[recordName])
  );
}

function mergedForDoc(existing: t | undefined, provided: t | undefined): t {
  if (!existing) {
    assert(provided);
    return provided;
  } else if (!provided) {
    assert(existing);
    return existing;
  } else {
    assert(existing && provided);
    return {
      ...provided,
      assignments:
        TargetAssignment.merged(
          existing.assignments,
          provided.assignments),
      doc_tags: [
        ...(
          /* Could preserve order ... if that matters. Whatever. */
          new Set([...existing.doc_tags, ...provided.doc_tags])
        )
      ],
      notes: mergeNotes(
        provided.notes,
        existing.notes),
    };
  }
}

function mergeNotes(s1: string | undefined, s2: string | undefined): string | undefined {
  if (!s1) {
    return s2;
  } else if (!s2) {
    return s2;
  } else if (s1.includes(s2)) { // Hack?
    return s1;
  } else if (s2.includes(s1)) { // Hack?
    return s2;
  } else {
    return `${s1}\n\n${s2}`;
  }
}

export function withoutField(recordTargets: t, field: string): t {
  return {
    ...recordTargets,
    assignments:
      recordTargets.assignments.filter(
        assignment => assignment.field != field),
  };
}
