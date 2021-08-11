import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Predicate from 'studio/blueprint/predicate';
import {UUID} from 'studio/util/types';

export type AtomScore = {
  type: 'atom_score';
  score: number;
};

export type ConnectiveScore = {
  type: 'conjunction_score' | 'disjunction_score';
  score: number;
  rule_scores: Partial<Record<string, RuleScore>>;
};

export type ConjunctionScore = ConnectiveScore & {
  type: 'conjunction_score';
};

export type DisjunctionScore = ConnectiveScore & {
  type: 'disjunction_score';
};

export type RuleScore =
  | AtomScore
  | ConnectiveScore
;

export type Atom = {
  type: 'atom';
  fields: string[];
  predicate: Predicate.t;
  name: string | undefined;
  uuid: UUID;

  // document: Optional[Document]
};

export type Connective =
  | Conjunction
  | Disjunction
;

export type Conjunction = {
  type: 'conjunction';
  rules: t[];
  name: string | undefined;
  uuid: string;

  // document: Optional[Document]
};

export type Disjunction = {
  type: 'disjunction';
  rules: t[];
  name: string | undefined;
  uuid: string;

  // document: Optional[Document]
};

export type t =
  | Atom
  | Connective
;

export function isConnective(rule: t): rule is Connective {
  switch (rule.type) {
    case 'atom':
      return false;
    case 'conjunction':
    case 'disjunction':
      return true;
  }
}

export function isConnectiveScore(ruleScore: RuleScore):
  ruleScore is ConnectiveScore
{
  switch (ruleScore.type) {
    case 'atom_score':
      return false;
    case 'conjunction_score':
    case 'disjunction_score':
      return true;
  }
}

export const fields = memo(
  function(rule: t): Set<string> {
    if (rule.type == 'atom') {
      return new Set(rule.fields);
    } else {
      const result = new Set<string>();
      rule.rules.forEach(
        rule => {
          fields(rule).forEach(
            field => result.add(field)
          );
        }
      );
      return result;
    }
  },
  { max: 200 },
);

export const fieldsInOrder = memo(
  function(rule: t): string[] {
    if (rule.type == 'atom') {
      return rule.fields;
    } else {
      const result: string[] = [];
      const set = new Set<string>();
      rule.rules.forEach(
        rule => {
          fields(rule).forEach(
            field => {
              if (!set.has(field)) {
                result.push(field);
                set.add(field);
              }
            }
          );
        }
      );
      return result;
    }
  },
  { max: 200 },
);

export function hasField(rule: t, field: string): boolean {
  return fields(rule).has(field);
}

export function numFields(rule: t): number {
  return fields(rule).size;
}

function inclusiveRange(start: number, end: number): number[] {
  const result = [];
  for (let i = start; i <= end; ++i) {
    result.push(i);
  }
  return result;
}

export function displayName(rule: t): string {
  if (rule.name != undefined) {
    return rule.name;
  } else {
    switch (rule.type) {
      case 'atom':
        return Predicate.displayName(rule.predicate);
      case 'conjunction':
        return 'conjunction';
      case 'disjunction':
        return 'disjunction';
    }
  }
}

export const asDict = memo(
  function(
    rules: Array<t>):
      Partial<Record<string, t>>
  {
    const result: Partial<Record<string, t>> = {};
    function incorporate(rule: t) {
      if (rule.uuid in result) {
        console.error('Multiple rules with same UUID; ignoring', rule.uuid, rules);
      }
      result[rule.uuid] = rule;
      if (isConnective(rule)) {
        rule.rules.forEach(incorporate);
      }
    }
    rules.forEach(incorporate);
    return result;
  },
  { max: 20 },
);
