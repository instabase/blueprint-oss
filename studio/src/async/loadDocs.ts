import memo from 'memoizee';

import {hasOwnProperty, isArray} from 'studio/util/types';

type DocName = string;

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

type DocBlob = {
  layouts: Layouts;
  lines: Array<Array<WordPolyDict>>;
};

type Response = {
  docs: Record<DocName, DocBlob>;
  errors?: Array<any>;
};

function validateResponse(response: Response): void {
  if (!hasOwnProperty(response, 'docs')) {
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
    'load-all-docs'
  );

  const blob = await response.json();

  validateResponse(blob);

  return blob;
}

export const loadResponse = memo(rawLoadResponse);

export const loadDocNames = memo(
  async function(samplesPath: string): Promise<string[]> {
    const response = await loadResponse(samplesPath);
    return [...Object.keys(response.docs)];
  }
);

export const loadDocBlob = memo(
  async function(samplesPath: string, docName: string): Promise<DocBlob> {
    const response = await loadResponse(samplesPath);
    return response.docs[docName];
  }
);

export const loadWordPolys = memo(
  async function(
    samplesPath: string,
    docName: string,
  ): Promise<WordPolyDict[]>
  {
    const doc = await loadDocBlob(samplesPath, docName);
    return doc.lines.flat();
  }
);

export const loadLayouts = memo(
  async function(
    samplesPath: string,
    docName: string,
  ): Promise<Layouts>
  {
    const doc = await loadDocBlob(samplesPath, docName);
    return doc.layouts;
  }
);

export function loadDocNamesFromResponse(response: Response): string[] {
  return [...Object.keys(response.docs)];
}

export function loadDocBlobFromResponse(response: Response, docName: string): DocBlob {
  return response.docs[docName];
}

export function loadWordPolysFromResponse(response: Response, docName: string): WordPolyDict[] {
  const doc = loadDocBlobFromResponse(response, docName);
  return doc.lines.flat();
}

export function loadLayoutsFromResponse(response: Response, docName: string): Layouts {
  const doc = loadDocBlobFromResponse(response, docName);
  return doc.layouts;
}
