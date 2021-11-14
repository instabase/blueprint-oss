import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Results from 'studio/blueprint/results';

import * as DocRun from 'studio/state/docRun';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

export type t = {
  uuid: UUID;
  modelIndex: number;
  docRuns: Array<DocRun.t>;
  keep: boolean;
  pin: boolean;
  startTime_ms: number;
};

export function build(
  modelIndex: number,
  docRuns: Array<DocRun.t>,
  keep: boolean,
  pin: boolean,
): t {
  return {
    uuid: uuidv4(),
    modelIndex,
    docRuns,
    keep,
    pin,
    startTime_ms: Date.now(),
  };
}

export const resultsForDoc = memo(
  function(
    // The first model run that has a run for this doc will be used.
    modelRuns: Array<t>,
    docName: string | undefined):
      Results.t | undefined
  {
    if (docName != undefined) {
      for (let modelRun of modelRuns) {
        const run = docRun(modelRun, docName);
        if (run) {
          if (run.type == 'FinishedDocRun') {
            return run.results;
          } else {
            return undefined;
          }
        }
      }
    }
  },
  { max: 1000 },
);

export function docRun(
  modelRun: t,
  docName: string):
    DocRun.t | undefined
{
  return runsByDoc(modelRun)[docName];
}

export const runsByDoc = memo(
  function(
    modelRun: t):
      Partial<Record<string, DocRun.t>>
  {
    const result: Partial<Record<string, DocRun.t>> = {};
    modelRun.docRuns.forEach(
      docRun => {
        assert(!(docRun.docName in result));
        result[docRun.docName] = docRun;
      }
    );
    return result;
  },
  { max: 20 },
);

export const hasPendingDocRuns = memo(
  function(modelRun: t): boolean {
    return pendingDocRuns(modelRun).length > 0;
  },
  { max: 100 },
);

export const pendingModelRuns = memo(
  function(modelRuns: Readonly<Array<t>>):
    Array<t>
  {
    return modelRuns.filter(hasPendingDocRuns);
  },
  { max: 50 },
);

export const pendingDocRuns = memo(
  function(modelRun: t):
    Array<DocRun.PendingDocRun>
  {
    return modelRun.docRuns.filter(DocRun.isPending);
  },
  { max: 100 },
);

export const finalizedDocRuns = memo(
  function(modelRun: t):
    Array<DocRun.FinalizedDocRun>
  {
    return modelRun.docRuns.filter(DocRun.isFinalized);
  },
  { max: 100 },
);

export const pendingModelDocRuns = memo(
  function(modelRuns: Readonly<Array<t>>):
    Array<DocRun.PendingDocRun>
  {
    return modelRuns.map(pendingDocRuns).flat();
  },
  { max: 50 },
);

export function numDocRuns(modelRun: t): number {
  return modelRun.docRuns.length;
}

export function numPendingDocRuns(modelRun: t): number {
  return pendingDocRuns(modelRun).length;
}

export function numFinalizedDocRuns(modelRun: t): number {
  return finalizedDocRuns(modelRun).length;
}
