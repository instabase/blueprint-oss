import assert from 'studio/util/assert';

export type NotLoaded<T> = {
  status: 'NotLoaded';
};

export type NotAvailable<T> = {
  status: 'NotAvailable';
};

export type Loading<T> = {
  status: 'Loading';
  promise: Promise<T>;
};

export type Done<T> = {
  status: 'Done';
  value: T;
};

export type Failed<T> = {
  status: 'Failed';
  errorCode: number;
  errorMessage: string;
};

export type Status =
  | 'NotLoaded'
  | 'NotAvailable'
  | 'Loading'
  | 'Done'
  | 'Failed'
;

export type t<T> =
  | NotLoaded<T>
  | NotAvailable<T>
  | Loading<T>
  | Done<T>
  | Failed<T>
;

export function finished<T>(
  resource: t<T> | undefined):
    T | undefined
{
  if (resource == undefined) {
    return undefined;
  } else if (resource.status == 'Done') {
    return resource.value;
  } else {
    return undefined;
  }
}

export function isDone<T>(resource: t<T>): resource is Done<T> {
  return resource.status == 'Done';
}

export function isFailed<T>(resource: t<T>): resource is Failed<T> {
  return resource.status == 'Failed';
}

export function worstStatus(statuses: Status[]): Status {
  if (statuses.some(status => status == 'Failed')) {
    return 'Failed';
  } else if (statuses.some(status => status == 'NotAvailable')) {
    return 'NotAvailable';
  } else if (statuses.some(status => status == 'NotLoaded')) {
    return 'NotLoaded';
  } else if (statuses.some(status => status == 'Loading')) {
    return 'Loading';
  } else {
    assert(statuses.every(status => status == 'Done'));
    return 'Done';
  }
}
