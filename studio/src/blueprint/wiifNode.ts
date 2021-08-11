import memo from 'memoizee';

import * as Entity from 'studio/foundation/entity';

import * as Rule from 'studio/blueprint/rule';

import * as Project from 'studio/state/project';

import {UUID} from 'studio/util/types';

export type t = {
  node_uuid: string;
  wiif_scores: {
    [rule_uuid: string]: Rule.RuleScore;
  };
  child_nodes: t[];
  uuid: UUID;
};

export const ruleScoresAsDict = memo(
  function(wiifNode: t):
    Partial<Record<string, Rule.RuleScore>>
  {
    const result: Partial<Record<string, Rule.RuleScore>> = {};

    function incorporate(
      ruleScores: Partial<Record<string, Rule.RuleScore>>)
    {
      Object.entries(ruleScores).forEach(
        ([ruleUUID, ruleScore]) => {
          if (ruleScore == undefined) {
            console.error(`Rule score for ${ruleUUID} is undefined; ignoring`);
          } else if (ruleUUID in result) {
            console.error(`Rule score for ${ruleUUID} appears multiple times; ignoring`);
          } else {
            result[ruleUUID] = ruleScore;

            if (Rule.isConnectiveScore(ruleScore)) {
              incorporate(ruleScore.rule_scores);
            }
          }
        }
      );
    }

    incorporate(wiifNode.wiif_scores);
    return result;
  },
  { max: 20 },
);

export function scoreForRule(node: t, ruleUUID: string): number | undefined {
  return ruleScoresAsDict(node)[ruleUUID]?.score;
}
