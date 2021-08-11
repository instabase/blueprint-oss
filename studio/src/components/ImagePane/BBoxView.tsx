import React from 'react';
import * as BBox from 'studio/foundation/bbox';
import './BBoxView.css';

type Props = {
  bbox: BBox.t;
  docBBox: BBox.t; // XXX: Rename to containerBBox or something.
  className?: string;
};

function BBoxView(props: Props, ref: React.ForwardedRef<unknown>) {
  return (
    <div
      className={'BBoxView ' + (props.className || '')}
      style={positionAbsolutely(props)}
      ref={ref as any}
    />
  );
}

export default React.forwardRef(
    (props: Props, ref) => BBoxView(props, ref));

function positionAbsolutely(props: Props) {
  const percentageFromLeft =
    100 * BBox.percentageFromLeft(
      BBox.upperLeft(props.bbox),
      props.docBBox);
  const percentageFromRight =
    100 * BBox.percentageFromRight(
      BBox.upperRight(props.bbox),
      props.docBBox);
  const percentageFromTop =
    100 * BBox.percentageFromTop(
      BBox.upperLeft(props.bbox),
      props.docBBox);
  const percentageFromBottom =
    100 * BBox.percentageFromBottom(
      BBox.lowerRight(props.bbox),
      props.docBBox);
  return {
    position: 'absolute' as 'absolute',
    left: `${percentageFromLeft}%`,
    right: `${percentageFromRight}%`,
    top: `${percentageFromTop}%`,
    bottom: `${percentageFromBottom}%`,
  };
}
