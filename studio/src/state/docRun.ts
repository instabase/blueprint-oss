import {v4 as uuidv4} from 'uuid';

import * as Results from 'studio/blueprint/results';

import {UUID} from 'studio/util/types';
import assert from 'studio/util/assert';

export type t =
  | PendingDocRun
  | FinalizedDocRun
;

export type PendingDocRun =
  | RequestedDocRun
  | ActiveDocRun
;

export type FinalizedDocRun =
  | FinishedDocRun
  | CanceledDocRun
  | FailedDocRun
;

export type RequestedDocRun = {
  type: 'RequestedDocRun';
  uuid: UUID;
  docName: string;
};

export type ActiveDocRun = {
  type: 'ActiveDocRun';
  uuid: UUID;
  docName: string;
};

export type FinishedDocRun = {
  type: 'FinishedDocRun';
  uuid: UUID;
  docName: string;
  results: Results.t;
};

export type CanceledDocRun = {
  type: 'CanceledDocRun';
  uuid: UUID;
  docName: string;
};

export type FailedDocRun = {
  type: 'FailedDocRun';
  uuid: UUID;
  docName: string;
  error: string;
};

export function isPending(docRun: t): docRun is PendingDocRun {
  switch (docRun.type) {
    case 'RequestedDocRun':
    case 'ActiveDocRun':
      return true;
    case 'FinishedDocRun':
    case 'CanceledDocRun':
    case 'FailedDocRun':
      return false;
  }
}

export function isFinalized(docRun: t): docRun is FinalizedDocRun {
  switch (docRun.type) {
    case 'RequestedDocRun':
    case 'ActiveDocRun':
      return false;
    case 'FinishedDocRun':
    case 'CanceledDocRun':
    case 'FailedDocRun':
      return true;
  }
}

export function build(docName: string): RequestedDocRun {
  return {
    type: 'RequestedDocRun',
    uuid: uuidv4(),
    docName,
  };
}

export function results(docRun: t):
  Results.t | undefined
{
  switch (docRun.type) {
    case 'FinishedDocRun':
      return docRun.results;
    case 'RequestedDocRun':
    case 'ActiveDocRun':
    case 'CanceledDocRun':
    case 'FailedDocRun':
      return undefined;
  }
}
