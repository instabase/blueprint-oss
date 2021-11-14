import React from 'react';

import * as BBox from 'studio/foundation/bbox';
import * as Doc from 'studio/foundation/doc';
import * as Entity from 'studio/foundation/entity';
import * as Text from 'studio/foundation/text';

import * as Project from 'studio/state/project';

import EntityView from './EntityView';
import {Options} from 'studio/hooks/useOptions';
import assert from 'studio/util/assert';

type Props = {
  project: Project.t;
  docName: string;
  doc: Doc.t;
  entityTypeOptions: Options;
};

export default function EntitiesOverlay(props: Props) {
  const deps = [
    props.project.selectionMode,
    props.entityTypeOptions,
  ];

  const entityTypesToShow = React.useMemo(() => {
    switch (props.project.selectionMode.type) {
      case 'Field':
        return ['Text'];
      case 'Rule':
        return [];
      case 'None':
        return Object.keys(props.entityTypeOptions)
          .filter(typeName => props.entityTypeOptions[typeName].checked)
          .sort();
    }
  }, deps);

  const entityFilter = React.useCallback((entity: Entity.t): boolean => {
    switch (props.project.selectionMode.type) {
      case 'Field':
        return (entity as Text.t).words.length == 1;
      case 'Rule':
      case 'None':
        return true;
    }
  }, deps);

  return <>
    {entityTypesToShow.map(entityType => (
      <React.Fragment key={props.docName + '-' + entityType}>
        {
          Doc.entitiesHavingType(props.doc, entityType as Entity.Type)
            .filter(entityFilter)
            .map((entity, index) =>
              <EntityView
                key={index.toString()}
                entity={entity}
                docBBox={props.doc.bbox as BBox.t}
              />
            )
        }
      </React.Fragment>
    ))}
  </>;
}
