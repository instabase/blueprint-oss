
import React from 'react';
import BBoxView from './BBoxView';
import * as BBox from 'studio/foundation/bbox';
import * as Entity from 'studio/foundation/entity';

type Props = {
  entity: Entity.t;
  docBBox: BBox.t;
};

export default function EntityView(props: Props) {
  return (
    <BBoxView
      bbox={props.entity.bbox}
      docBBox={props.docBBox}
      className="ImagePane_ExtractedValueView"
    />
  );
}
