import memo from 'memoizee';

import * as RecordTargets from 'studio/foundation/recordTargets';

import * as Node from 'studio/blueprint/node';

export type t = RecordTargets.t & {
  discriminator: 'NodeRecordTargets';
};

export const build = memo(
  function(node: Node.t, recordTargets: RecordTargets.t): t {
    return {
      ...recordTargets,
      discriminator: 'NodeRecordTargets',
      assignments: recordTargets.assignments.filter(
        assignment => Node.hasField(node, assignment.field)
      ),
    };
  },
  { max: 50 },
);
