import React from 'react';

import * as Results from 'studio/blueprint/results';
import * as Scoring from 'studio/blueprint/scoring';

import * as ModelRun from 'studio/state/modelRun';
import * as Project from 'studio/state/project';

import {Props as DropdownProps} from 'studio/components/Dropdown';

export type Extractions = DropdownProps<Scoring.ScoredExtraction>;

export default function useExtractions(project: Project.t): Extractions {
  const model = Project.model(project);
  const docName = project.selectedDocName;
  const node = Project.selectedNode(project);
  const results =
    ModelRun.resultsForDoc(
      Project.modelRunsForCurrentModel(project),
      project.selectedDocName);
  const extractions =
    (node &&
     results &&
     Results.extractions(Results.byNode(results)[node.uuid]))
    || [];

  let [selectedExtraction, setSelectedExtraction] =
    React.useState<Scoring.ScoredExtraction | undefined>(undefined);

  if (selectedExtraction == undefined ||
      !extractions.includes(selectedExtraction))
  {
    if (extractions.length > 0) {
      setSelectedExtraction(extractions[0]);
      selectedExtraction = extractions[0];
    } else if (selectedExtraction != undefined) {
      setSelectedExtraction(undefined);
      selectedExtraction = undefined;
    }
  }

  const extractionToNumber = new Map<Scoring.ScoredExtraction, string>();
  extractions.forEach(
    (extraction, index) =>
      extractionToNumber.set(
        extraction,
        '#' + (index + 1).toString()));

  return {
    options: extractions,
    selected: selectedExtraction,
    stringify: extraction => extractionToNumber.get(extraction) as string,
    onSelected: extraction => setSelectedExtraction(extraction),
  };
}
