import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Results from 'studio/blueprint/results';

import * as RecordRun from 'studio/state/recordRun';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

export type t = {
  uuid: UUID;
  modelIndex: number;
  recordRuns: Array<RecordRun.t>;
  keep: boolean;
  pin: boolean;
  startTime_ms: number;
};

export function build(
  modelIndex: number,
  recordRuns: Array<RecordRun.t>,
  keep: boolean,
  pin: boolean,
): t {
  return {
    uuid: uuidv4(),
    modelIndex,
    recordRuns,
    keep,
    pin,
    startTime_ms: Date.now(),
  };
}

export const resultsForDoc = memo(
  function(
    // The first model run that has a run for this doc will be used.
    modelRuns: Array<t>,
    recordName: string | undefined):
      Results.t | undefined
  {
    if (recordName != undefined) {
      for (let modelRun of modelRuns) {
        const run = recordRun(modelRun, recordName);
        if (run) {
          if (run.type == 'FinishedRecordRun') {
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

export function recordRun(
  modelRun: t,
  recordName: string):
    RecordRun.t | undefined
{
  return runsByDoc(modelRun)[recordName];
}

export const runsByDoc = memo(
  function(
    modelRun: t):
      Partial<Record<string, RecordRun.t>>
  {
    const result: Partial<Record<string, RecordRun.t>> = {};
    modelRun.recordRuns.forEach(
      recordRun => {
        assert(!(recordRun.recordName in result));
        result[recordRun.recordName] = recordRun;
      }
    );
    return result;
  },
  { max: 20 },
);

export const hasPendingRecordRuns = memo(
  function(modelRun: t): boolean {
    return pendingRecordRuns(modelRun).length > 0;
  },
  { max: 100 },
);

export const pendingModelRuns = memo(
  function(modelRuns: Readonly<Array<t>>):
    Array<t>
  {
    return modelRuns.filter(hasPendingRecordRuns);
  },
  { max: 50 },
);

export const pendingRecordRuns = memo(
  function(modelRun: t):
    Array<RecordRun.PendingRecordRun>
  {
    return modelRun.recordRuns.filter(RecordRun.isPending);
  },
  { max: 100 },
);

export const finalizedRecordRuns = memo(
  function(modelRun: t):
    Array<RecordRun.FinalizedRecordRun>
  {
    return modelRun.recordRuns.filter(RecordRun.isFinalized);
  },
  { max: 100 },
);

export const pendingModelRecordRuns = memo(
  function(modelRuns: Readonly<Array<t>>):
    Array<RecordRun.PendingRecordRun>
  {
    return modelRuns.map(pendingRecordRuns).flat();
  },
  { max: 50 },
);

export function numRecordRuns(modelRun: t): number {
  return modelRun.recordRuns.length;
}

export function numPendingRecordRuns(modelRun: t): number {
  return pendingRecordRuns(modelRun).length;
}

export function numFinalizedRecordRuns(modelRun: t): number {
  return finalizedRecordRuns(modelRun).length;
}
