import React from 'react';

import Image from 'studio/components/ImagePane/Image';

import * as Transform from 'studio/util/zoomAndPanTransform';

import {Layouts} from 'studio/async/loadDocs';

import './ImageStack.css';

type Props = {
  children: React.ReactNode;
  layouts: Layouts;
  transform: Transform.t;
};

function sum(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0);
}

export default (props: Props) => {
  const width = Math.max(...Object.values(props.layouts).map(layout => layout.width));
  const height = sum(Object.values(props.layouts).map(layout => layout.height));

  const style = {
    transform: `
      translate(-50%, -50%)
      translate(${props.transform.x}px, ${props.transform.y}px)
      scale(${props.transform.scale})
    `,
    width,
    height,
  };

  return (
    <div
      className="ImagePane_ImageStack"
      style={style}
    >
      {
        Object.values(props.layouts).map(
          layout => (
            <Image
              layout={layout}
              key={layout.processed_image_path}
            />
          ),
        )
      }
      {props.children}
    </div>
  );
};
