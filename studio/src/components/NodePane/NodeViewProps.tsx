import * as Doc from 'studio/foundation/doc';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as Scoring from 'studio/blueprint/scoring';

import * as NodeDocTargets from 'studio/state/nodeDocTargets';
import * as Project from 'studio/state/project';

import {Props as DropdownProps} from 'studio/components/Dropdown';

type NodeViewProps = {
  project: Project.t;
  docName: string | undefined,
  doc: Doc.t | undefined;
  targets: NodeDocTargets.t | undefined;
  model: Model.t;
  node: Node.t;
  path: Model.Path;
  extractions: DropdownProps<Scoring.ScoredExtraction>;
};

export default NodeViewProps;
