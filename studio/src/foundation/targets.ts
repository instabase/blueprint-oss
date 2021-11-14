import memo from 'memoizee';

import * as Doc from 'studio/foundation/doc';
import * as DocTargets from 'studio/foundation/docTargets';
import * as Schema from 'studio/foundation/targetsSchema';
import * as TargetValue from 'studio/foundation/targetValue';
import * as Entity from 'studio/foundation/entity';

type DocTagDescription = {
  short: string | undefined;
  long: string | undefined;
};

type DocTags = Partial<Record<string, DocTagDescription>>;

export type t = {
  doc_targets: DocTargets.t[];
  schema: Schema.t;
  doc_tags: DocTags;

  // output_config
  // field_groups
};

export function build(): t {
  return {
    doc_targets: [],
    schema: Schema.build(),
    doc_tags: {},
  };
}

export function tagsPresentInSomeDoc(targets: t): string[] {
  const result: string[] = [];
  for (let docTargets of targets.doc_targets) {
    for (let tag of docTargets.doc_tags) {
      if (!result.includes(tag)) {
        result.push(tag);
      }
    }
  }
  return result;
}

export const docNames = memo(
  function(targets: t): string[] {
    return targets.doc_targets.map(
      docTargets => docTargets.doc_name
    );
  }
);

export function docTargets(
  targets: t,
  docName: string):
    DocTargets.t | undefined
{
  return asDict(targets)[docName];
}

export const asDict = memo(
  function(targets: t):
    Partial<Record<string, DocTargets.t>>
  {
    return DocTargets.asDocNameDict(targets.doc_targets);
  }
);

export function fields(targets: t): string[] {
  return Schema.fields(targets.schema);
}

export function hasField(targets: t, field: string): boolean {
  return Schema.hasField(targets.schema, field);
}

export type FieldValuePair = [string, TargetValue.t | undefined];

export function fieldValuePairs(
  targets: t,
  docName: string):
    FieldValuePair[] | undefined
{
  const theseDocTargets = docTargets(targets, docName);
  if (theseDocTargets != undefined) {
    return Schema.fieldValuePairs(
      targets.schema,
      theseDocTargets);
  }
}

export function merged(existing: t, provided: t): t {
  return populateSchema({
    doc_targets: DocTargets.merged(existing.doc_targets, provided.doc_targets),
    schema:
      provided.schema
        ? Schema.merged(existing.schema, provided.schema)
        : existing.schema,
    doc_tags:
      provided.doc_tags
        ? mergedDocTags(existing.doc_tags, provided.doc_tags)
        : existing.doc_tags,
  });
}

export function populateSchema(targets: t): t {
  const schema = [...targets.schema];

  targets.doc_targets.forEach(
    docTargets => {
      docTargets.assignments.forEach(
        ({field}) => {
          if (!Schema.hasField(schema, field)) {
            schema.push({
              field,
              type: Entity.heuristicDefaultType(field),
              is_label: Entity.heuristicDefaultIsLabel(field),
            });
          }
        }
      );
    }
  );

  return {...targets, schema};
}

function mergedDocTags(existing: DocTags, provided: DocTags) {
  const keys = new Set([...Object.keys(existing), ...Object.keys(provided)]);
  const result: DocTags = {};
  keys.forEach(
    key => {
      result[key] = {
        short: existing[key]?.short || provided[key]?.short,
        long: existing[key]?.long || provided[key]?.long,
      };
    }
  );
  return result;
}

export function withoutField(targets: t, field: string): t {
  return {
    ...targets,
    doc_targets:
      targets.doc_targets.map(
        docTargets =>
          DocTargets.withoutField(
            docTargets,
            field)),
    schema: Schema.withoutField(targets.schema, field),
  };
}
