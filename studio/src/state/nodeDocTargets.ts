import memo from 'memoizee';

import * as DocTargets from 'studio/foundation/docTargets';

import * as Node from 'studio/blueprint/node';

export type t = DocTargets.t & {
  discriminator: 'NodeDocTargets';
};

export const build = memo(
  function(node: Node.t, docTargets: DocTargets.t): t {
    return {
      ...docTargets,
      discriminator: 'NodeDocTargets',
      assignments: docTargets.assignments.filter(
        assignment => Node.hasField(node, assignment.field)
      ),
    };
  },
  { max: 50 },
);
