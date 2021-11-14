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

export function build(docName: string): t {
  return {
    doc_name: docName,
    assignments: [],
    doc_tags: [],
    notes: undefined,
  };
}

export function isEmpty(docTargets: t): boolean {
  return fields(docTargets).length == 0;
}

export const fields = memo(
  function(docTargets: t): string[] {
    return docTargets.assignments.map(
      ({field, value}) => field
    );
  }
);

export function hasValue(docTargets: t, field: string): boolean {
  return asDict(docTargets)[field] != undefined;
}

export function hasAllValues(docTargets: t, fields: string[]): boolean {
  return fields.every(field => hasValue(docTargets, field));
}

export function hasNonNullValue(docTargets: t, field: string): boolean {
  const value = asDict(docTargets)[field];
  return value != undefined && TargetValue.isNonNull(value);
}

export function hasAllNonNullValues(docTargets: t, fields: string[]): boolean {
  return fields.every(field => hasNonNullValue(docTargets, field));
}

export function hasPositionedValue(docTargets: t, field: string): boolean {
  const value = asDict(docTargets)[field];
  return value != undefined && TargetValue.isPositioned(value);
}

export function hasAllPositionedValues(docTargets: t, fields: string[]): boolean {
  return fields.every(field => hasPositionedValue(docTargets, field));
}

export const asDict = memo(
  function(
    docTargets: t):
      Partial<Record<string, TargetValue.t>>
  {
    const result: Partial<Record<string, TargetValue.t>> = {};
    docTargets.assignments.forEach(
      ({field, value}) => result[field] = value
    );
    return result;
  }
);

export const asDocNameDict = memo(
  function(docTargets: t[]):
    Partial<Record<string, t>>
  {
    const result: Partial<Record<string, t>> = {};
    docTargets.forEach(
      forDoc => {
        result[forDoc.doc_name] = forDoc;
      }
    );
    return result;
  }
);

export const value = memo(
  function(
    docTargets: t,
    field: string):
      TargetValue.t | undefined
  {
    return asDict(docTargets)[field];
  }
);

export function merged(existing: t[], provided: t[]): t[] {
  const existingDict = asDocNameDict(existing);
  const providedDict = asDocNameDict(provided);
  const docNames = new Set([...Object.keys(existingDict),
                            ...Object.keys(providedDict)]);
  return [...docNames].map(
    docName => mergedForDoc(existingDict[docName], providedDict[docName])
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

export function withoutField(docTargets: t, field: string): t {
  return {
    ...docTargets,
    assignments:
      docTargets.assignments.filter(
        assignment => assignment.field != field),
  };
}
