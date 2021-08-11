import React from 'react';
import memo from 'memoizee';
import {v4 as uuidv4} from 'uuid';

import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';
import * as Doc from 'studio/foundation/doc';

import * as Node from 'studio/blueprint/node';
import * as Rule from 'studio/blueprint/rule';
import * as Scoring from 'studio/blueprint/scoring';

import * as Project from 'studio/state/project';

import ExtractedValueView from './ExtractedValueView';
import {isNotUndefined} from 'studio/util/types';

import assert from 'studio/util/assert';
import {UUID} from 'studio/util/types';

import './ExtractedValuesOverlay.css';

type Props = {
  project: Project.t;
  doc: Doc.t;
  extraction: Extraction.t;
  extractedValuesChecked: boolean;
};

export default function ExtractedValuesOverlay(props: Props) {
  const fieldsToShow =
    fieldsForWhichToShowExtractedValues(
      props.project,
      props.extractedValuesChecked);

  const extractionID = uniqueExtractionID(props.extraction);

  return <>
    {
      props.extraction.assignments.filter(
        ({field}) => fieldsToShow.has(field)
      ).map(
        ({field, entity}, index) => (
          <ExtractedValueView
            key={extractionID + index.toString()}
            entity={entity}
            docBBox={props.doc.bbox}
          />
        )
      )
    }
  </>;
};

export const fieldsForWhichToShowExtractedValues = memo(
  function(project: Project.t, checkboxChecked: boolean): Set<string> {
    switch (project.selectionMode.type) {
      case 'None':
        const node = Project.selectedNode(project);
        if (node && checkboxChecked) {
          return new Set(Node.fields(node));
        } else {
          return new Set();
        }
      case 'Field':
        return new Set([project.selectionMode.field]);
      case 'Rule':
        const rule = Project.selectedRule(project);
        assert(rule);
        return Rule.fields(rule);
    }
  },
  { max: 10 },
);

const uniqueExtractionID = memo(
  function (extraction: Extraction.t): UUID {
    return uuidv4();
  }
);
