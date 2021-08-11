import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';

import * as Rule from 'studio/blueprint/rule';

import * as Project from 'studio/state/project';

import {UUID, isNotUndefined} from 'studio/util/types';

export type FieldScores = Partial<Record<string, number>>;

export type ScoredExtraction = {
  extraction: Extraction.t;
  score: number;
  field_scores: FieldScores;
  rule_scores: Partial<Record<UUID, Rule.RuleScore>>;
  uuid: UUID;
};

export function value(
  extraction: ScoredExtraction | undefined,
  field: string | undefined):
    Entity.t | undefined
{
  if (extraction == undefined || field == undefined) {
    return undefined;
  } else {
    return Extraction.value(extraction.extraction, field);
  }
}

export function hasValue(
  extraction: ScoredExtraction | undefined,
  field: string | undefined):
    boolean
{
  return value(extraction, field) != undefined;
}

export function ruleScore(
  extraction: ScoredExtraction,
  ruleUUID: UUID):
    Rule.RuleScore | undefined
{
  return extraction.rule_scores[ruleUUID];
}

export function extractedText(
  extraction: ScoredExtraction,
  field: string):
    string | undefined
{
  if (extraction == undefined) {
    return '(no extraction)';
  } else if (field == undefined) {
    return '(no field)';
  } else {
    const extractedValue = value(extraction, field);
    if (extractedValue != undefined) {
      return extractedValue.text;
    }
  }
}
