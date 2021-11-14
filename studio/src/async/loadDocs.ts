import memo from 'memoizee';

import * as Handle from 'studio/state/handle';
import loadImage from 'studio/async/loadImage';
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
  file_name: string;
  file_handle: Handle.FileHandle;
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

export async function rawLoadResponse(handle: Handle.t): Promise<Response> {
  console.log('Loading docs...');

  const blob: Response = {
    docs: {},
    errors: [],
  };

  const imagesHandle = await handle.getDirectoryHandle('img');
  for await (let [docName, imageHandle] of imagesHandle.entries()) {
    // XXX: This is slow, and we are doing it on project load.
    //      We could instead get the width/height when loading the image.
    //      Probably the easiest way to make that work is to delete
    //      the width/height properties from the Layout type above.
    const image = await loadImage(imageHandle);

    blob.docs[docName] = {
      layouts: {
        '0': { // "record name"
          width: image.width,
          height: image.height,
          file_name: docName,
          file_handle: imageHandle,
        },
      },
      lines: [
      ],
    };
  }
  console.log('Done loading image data', blob);

  const ocrFilesHandle = await handle.getDirectoryHandle('ocr');
  for await (let [ocrFileName, ocrFileHandle] of ocrFilesHandle.entries()) {
    // ...
  }
  console.log('Done loading ocr data', blob);

  return blob;
}

export const loadResponse = memo(rawLoadResponse);

export const loadDocNames = memo(
  async function(handle: Handle.t): Promise<string[]> {
    const response = await loadResponse(handle);
    return [...Object.keys(response.docs)];
  }
);

export const loadDocBlob = memo(
  async function(handle: Handle.t, docName: string): Promise<DocBlob> {
    const response = await loadResponse(handle);
    return response.docs[docName];
  }
);

export const loadWordPolys = memo(
  async function(
    handle: Handle.t,
    docName: string,
  ): Promise<WordPolyDict[]>
  {
    const doc = await loadDocBlob(handle, docName);
    return doc.lines.flat();
  }
);

export const loadLayouts = memo(
  async function(
    handle: Handle.t,
    docName: string,
  ): Promise<Layouts>
  {
    const doc = await loadDocBlob(handle, docName);
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
