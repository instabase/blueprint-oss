import React from 'react';

import {useDivRef} from 'studio/hooks/useDOMRef';
import useResource from 'studio/hooks/useResource';

import * as Transform from 'studio/util/zoomAndPanTransform';

import {Layout} from 'studio/async/loadRecords';
import loadImage from 'studio/async/loadImage';

type Props = {
  layout: Layout;
};

export default ({layout}: Props) => {
  const style = {
    width: layout.width,
    height: layout.height,
  };

  const imagePromise = loadImage(layout.processed_image_path);
  const imageResource = useResource(imagePromise);

  const ref = useDivRef();

  React.useEffect(
    () => {
      if (ref.current) {
        while (ref.current.lastChild) {
          ref.current.removeChild(ref.current.lastChild);
        }

        ref.current.append(
          imageResource.status == 'Done'
            ? imageResource.value
            : ''
        );
      }
    },
    [
      ref.current,
      imageResource.status,
    ],
  );

  return (
    <div
      className="ImagePane_ImageStack_ImageContainer"
      style={style}
      ref={ref}
    />
  );
};
