import memo from 'memoizee';

export async function loadImageAsBlob(url: string): Promise<Blob> {
  const response = await fetch(url);
  return response.blob();
}

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

export default memo(rawLoadImage, {max: 20});
