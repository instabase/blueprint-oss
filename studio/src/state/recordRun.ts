import {v4 as uuidv4} from 'uuid';

import * as Results from 'studio/blueprint/results';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

export type t =
  | PendingRecordRun
  | FinalizedRecordRun
;

export type PendingRecordRun =
  | RequestedRecordRun
  | ActiveRecordRun
;

export type FinalizedRecordRun =
  | FinishedRecordRun
  | CanceledRecordRun
  | FailedRecordRun
;

export type RequestedRecordRun = {
  type: 'RequestedRecordRun';
  uuid: UUID;
  recordName: string;
};

export type ActiveRecordRun = {
  type: 'ActiveRecordRun';
  uuid: UUID;
  recordName: string;
};

export type FinishedRecordRun = {
  type: 'FinishedRecordRun';
  uuid: UUID;
  recordName: string;
  results: Results.t;
};

export type CanceledRecordRun = {
  type: 'CanceledRecordRun';
  uuid: UUID;
  recordName: string;
};

export type FailedRecordRun = {
  type: 'FailedRecordRun';
  uuid: UUID;
  recordName: string;
  error: string;
};

export function isPending(recordRun: t): recordRun is PendingRecordRun {
  switch (recordRun.type) {
    case 'RequestedRecordRun':
    case 'ActiveRecordRun':
      return true;
    case 'FinishedRecordRun':
    case 'CanceledRecordRun':
    case 'FailedRecordRun':
      return false;
  }
}

export function isFinalized(recordRun: t): recordRun is FinalizedRecordRun {
  switch (recordRun.type) {
    case 'RequestedRecordRun':
    case 'ActiveRecordRun':
      return false;
    case 'FinishedRecordRun':
    case 'CanceledRecordRun':
    case 'FailedRecordRun':
      return true;
  }
}

export function build(recordName: string): RequestedRecordRun {
  return {
    type: 'RequestedRecordRun',
    uuid: uuidv4(),
    recordName,
  };
}

export function results(recordRun: t):
  Results.t | undefined
{
  switch (recordRun.type) {
    case 'FinishedRecordRun':
      return recordRun.results;
    case 'RequestedRecordRun':
    case 'ActiveRecordRun':
    case 'CanceledRecordRun':
    case 'FailedRecordRun':
      return undefined;
  }
}
