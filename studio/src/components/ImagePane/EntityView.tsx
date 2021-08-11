import React from 'react';
import BBoxView from './BBoxView';
import useDragSelectable from 'studio/hooks/useDragSelectable';
import * as BBox from 'studio/foundation/bbox';
import * as Entity from 'studio/foundation/entity';

type Props = {
  entity: Entity.t;
  docBBox: BBox.t;
  className?: string;
};

export default function EntityView(props: Props) {
  const [ref, _] = useDragSelectable(props.entity);
  return (
    <BBoxView
      bbox={props.entity.bbox}
      docBBox={props.docBBox}
      className={props.className}
      ref={ref}
    />
  );
}
