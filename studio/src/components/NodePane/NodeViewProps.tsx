import * as Doc from 'studio/foundation/doc';

import * as Model from 'studio/blueprint/model';
import * as Node from 'studio/blueprint/node';
import * as Scoring from 'studio/blueprint/scoring';

import * as NodeRecordTargets from 'studio/state/nodeRecordTargets';
import * as Project from 'studio/state/project';

import {Props as DropdownProps} from 'studio/components/Dropdown';

type NodeViewProps = {
  project: Project.t;
  recordName: string | undefined,
  doc: Doc.t | undefined;
  targets: NodeRecordTargets.t | undefined;
  model: Model.t;
  node: Node.t;
  path: Model.Path;
  extractions: DropdownProps<Scoring.ScoredExtraction>;
};

export default NodeViewProps;
