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
  const endpoint = 'wiif';
  console.log(`Hitting ${endpoint}`, doc, node, targetExtraction);
  const response = await fetch(`http://localhost:5000/${endpoint}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      'doc': doc,
      'node': node,
      'target_extraction': targetExtraction,
    }),
  });
  const responseJSON = await response.json();
  console.log(`Got response from ${endpoint}`, doc, node, targetExtraction, responseJSON);
  if ('error' in responseJSON) {
    console.log(`Error from ${endpoint}`, responseJSON);
    throw responseJSON;
  }
  return responseJSON['wiif_node'] as WiifNode.t;
}

export default memo(rawWIIF, {max: 100});
