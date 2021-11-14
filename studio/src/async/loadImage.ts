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
  // From https://stackoverflow.com/questions/11089732/display-image-from-blob-using-javascript-and-websockets
  function encode (input: any) {
    var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    var output = "";
    var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
    var i = 0;

    while (i < input.length) {
        chr1 = input[i++];
        chr2 = i < input.length ? input[i++] : Number.NaN; // Not sure if the index
        chr3 = i < input.length ? input[i++] : Number.NaN; // checks are needed here

        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;

        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }
        output += keyStr.charAt(enc1) + keyStr.charAt(enc2) +
                  keyStr.charAt(enc3) + keyStr.charAt(enc4);
    }
    return output;
  }

  const file = await handle.getFile();
  const arrayBuffer = await file.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  const img = document.createElement('img');
  img.src = `data:image/jpg;base64,${encode(bytes)}`;
  return img;
}

export default memo(rawLoadImage, {max: 20});
