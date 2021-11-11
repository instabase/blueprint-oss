import memo from 'memoizee';
import * as Handle from 'studio/state/handle';

export async function loadImageAsBlob(url: string): Promise<Blob> {
  const response = await fetch(url);
  return response.blob();
}

/*
function rawLoadImage(url: string): Promise<HTMLImageElement> {
  // console.debug(`Fetching image from ${url}`);
  return new Promise<HTMLImageElement>(
    (resolve, reject) => {
      const img = document.createElement('img');
      img.src = url;

      img.onload = () => {
        // console.debug(`Done loading image from ${url}`);
        resolve(img);
      };

      img.onerror = () => {
        console.error(`Error loading image from ${url}`);
        reject('Error loading image');
      };
    }
  );
}
*/

async function rawLoadImage(handle: Handle.FileHandle): Promise<HTMLImageElement> {
  const file = await handle.getFile();
  const text = await file.text();
  const img = document.createElement('img');
  img.src = `data:image/jpg;${text}`;
  return img;
}

export default memo(rawLoadImage, {max: 20});
