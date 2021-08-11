import memo from 'memoizee';
import * as Doc from 'studio/foundation/doc';
import * as Extraction from 'studio/foundation/extraction';
import * as Node from 'studio/blueprint/node';
import * as WiifNode from 'studio/blueprint/wiifNode';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {BlueprintSettings} from 'studio/state/settings';
import {stringify, writeString} from 'studio/util/stringifyForPython';

async function rawWIIF(
  doc: Doc.t,
  node: Node.t,
  targetExtraction: Extraction.t,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext,
): Promise<WiifNode.t>
{
  throw new Error('Not implemented');
}

export default memo(rawWIIF, {max: 100});
