import memo from 'memoizee';

import {hasOwnProperty, isArray} from 'studio/util/types';

type RecordName = string;

type WordPolyDict = {
  word: string;
  page: number;
  start_x: number;
  end_x: number;
  start_y: number;
  end_y: number;
};

export type Layout = {
  width: number;
  height: number;
  processed_image_path: string;
};

export type Layouts = Record<string, Layout>;

type RecordBlob = {
  layouts: Layouts;
  lines: Array<Array<WordPolyDict>>;
};

type Response = {
  records: Record<RecordName, RecordBlob>;
  errors?: Array<any>;
};

function validateResponse(response: Response): void {
  if (!hasOwnProperty(response, 'records')) {
    throw new Error();
  }

  if (hasOwnProperty(response, 'errors')) {
    /*
    if (!isArray(response.errors)) {
      throw new Error();
    }
    */
  }
}

export async function rawLoadResponse(samplesPath: string): Promise<Response> {
  const response = await fetch(
    'load-all-records'
  );

  const blob = await response.json();

  validateResponse(blob);

  return blob;
}

export const loadResponse = memo(rawLoadResponse);

export const loadRecordNames = memo(
  async function(samplesPath: string): Promise<string[]> {
    const response = await loadResponse(samplesPath);
    return [...Object.keys(response.records)];
  }
);

export const loadRecordBlob = memo(
  async function(samplesPath: string, recordName: string): Promise<RecordBlob> {
    const response = await loadResponse(samplesPath);
    return response.records[recordName];
  }
);

export const loadWordPolys = memo(
  async function(
    samplesPath: string,
    recordName: string,
  ): Promise<WordPolyDict[]>
  {
    const record = await loadRecordBlob(samplesPath, recordName);
    return record.lines.flat();
  }
);

export const loadLayouts = memo(
  async function(
    samplesPath: string,
    recordName: string,
  ): Promise<Layouts>
  {
    const record = await loadRecordBlob(samplesPath, recordName);
    return record.layouts;
  }
);

export function loadRecordNamesFromResponse(response: Response): string[] {
  return [...Object.keys(response.records)];
}

export function loadRecordBlobFromResponse(response: Response, recordName: string): RecordBlob {
  return response.records[recordName];
}

export function loadWordPolysFromResponse(response: Response, recordName: string): WordPolyDict[] {
  const record = loadRecordBlobFromResponse(response, recordName);
  return record.lines.flat();
}

export function loadLayoutsFromResponse(response: Response, recordName: string): Layouts {
  const record = loadRecordBlobFromResponse(response, recordName);
  return record.layouts;
}
