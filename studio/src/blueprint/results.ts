import memo from 'memoizee';

import * as DocTargets from 'studio/foundation/docTargets';
import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';

import * as Node from 'studio/blueprint/node';
import * as Scoring from 'studio/blueprint/scoring';

import {UUID, isNotUndefined} from 'studio/util/types';

export type DocRuntimeInfo = {
  loading_ms: number | undefined;
  binding_ms: number | undefined;
  pumping_ms: number | undefined;
  total_ms: number | undefined;

  timed_out: boolean;
};

export type ResultsNode = {
  node_uuid: string;
  top_20_extractions: Scoring.ScoredExtraction[];
  top_score: number;
  child_nodes: ResultsNode[];
};

export type t = {
  root: ResultsNode | undefined;
  runtime_info: DocRuntimeInfo;
};

export const byNode = memo(
  function(results: t):
    Partial<Record<UUID, ResultsNode>>
  {
    const result: Partial<Record<UUID, ResultsNode>> = {};
    if (results.root == undefined) {
      return result;
    }
    function populate(node: ResultsNode) {
      result[node.node_uuid] = node;
      node.child_nodes.forEach(populate);
    }
    populate(results.root);
    return result;
  },
  { max: 20 },
);

export function bestExtractionScore(
  results: t | undefined, node: Node.t):
    number | undefined
{
  return results && byNode(results)[node.uuid]?.top_score;
}

export function bestOverallExtractionScore(results: t): number {
  return results.root ? results.root.top_score : 0;
}

export function bestExtraction(results: t): Extraction.t | undefined {
  if (results.root) {
    return results.root.top_20_extractions[0].extraction;
  }
}

export function extractions(
  resultsNode: ResultsNode | undefined):
    Scoring.ScoredExtraction[] | undefined
{
  if (resultsNode != undefined) {
    return resultsNode.top_20_extractions;
  }
}
