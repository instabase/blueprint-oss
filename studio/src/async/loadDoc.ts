import memo from 'memoizee';
import * as Doc from 'studio/foundation/doc';
import {loadDocBlob} from 'studio/async/loadDocs';
import * as Project from 'studio/state/project';
import {BlueprintSettings} from 'studio/state/settings';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {stringify, writeString} from 'studio/util/stringifyForPython';
import * as Handle from 'studio/state/handle';

async function onDiskGoogleOCRFileHandle(
  handle: Handle.t,
  docName: string):
    Promise<Handle.FileHandle>
{
  const subdirHandle = await handle.getDirectoryHandle('ocr');
  return subdirHandle.getFileHandle(`${docName}.json`);
}

async function onDiskTesseractOCRFileHandle(
  handle: Handle.t,
  docName: string):
    Promise<Handle.FileHandle>
{
  const subdirHandle = await handle.getDirectoryHandle('hocr');
  return subdirHandle.getFileHandle(`${docName}.hocr`);
}

async function rawLoadDoc(
  handle: Handle.t,
  docName: string,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext):
    Promise<Doc.t>
{
  let googleOCR: any;
  let tesseractOCR: any;

  try {
    const fileHandle = await onDiskGoogleOCRFileHandle(handle, docName);
    console.log('Got Google OCR filehandle for doc', fileHandle);
    const file = await fileHandle.getFile();
    const text = await file.text();
    googleOCR = JSON.parse(text);
    console.log('Loaded raw Google OCR doc', googleOCR);
  } catch {
    console.log('Did not find Google OCR data');
  }

  try {
    const fileHandle = await onDiskTesseractOCRFileHandle(handle, docName);
    console.log('Got Tesseract OCR filehandle for doc', fileHandle);
    const file = await fileHandle.getFile();
    const text = await file.text();
    tesseractOCR = text;
    console.log('Loaded raw Tesseract OCR doc', tesseractOCR);
  } catch {
    console.log('Did not find Tesseract OCR data');
  }

  const endpoint = 'gen_bp_doc';
  console.log(`Hitting ${endpoint}`, handle, docName);
  const response = await fetch(`http://localhost:5000/${endpoint}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      'google_ocr': googleOCR,
      'tesseract_ocr': tesseractOCR,
    }),
  });
  const responseJSON = await response.json();
  console.log(`Got response from ${endpoint}`, handle, docName, responseJSON);
  if ('error' in responseJSON) {
    console.log(`Error from ${endpoint}`, responseJSON);
    throw responseJSON;
  }
  return responseJSON['doc'] as Doc.t;
}

const loadDoc = memo(rawLoadDoc, {max: 500});

export default loadDoc;
