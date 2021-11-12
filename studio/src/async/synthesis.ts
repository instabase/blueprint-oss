import * as Doc from 'studio/foundation/doc';
import * as Extraction from 'studio/foundation/extraction';
import * as TargetsSchema from 'studio/foundation/targetsSchema';
import * as PatternNode from 'studio/blueprint/patternNode';
import {Value as TheSessionContext} from 'studio/context/SessionContext';
import {BlueprintSettings} from 'studio/state/settings';
import {stringify, writeString} from 'studio/util/stringifyForPython';

export default async function synthesis(
  doc: Doc.t,
  targetExtraction: Extraction.t,
  schema: TargetsSchema.t,
  blueprintSettings: BlueprintSettings,
  sessionContext: TheSessionContext,
): Promise<PatternNode.t>
{
  const endpoint = 'synthesis';
  console.log(`Hitting ${endpoint}`, doc, targetExtraction, schema);
  const response = await fetch(`http://localhost:5000/${endpoint}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      'doc': doc,
      'target_extraction': targetExtraction,
      'schema': schema,
    }),
  });
  const responseJSON = await response.json();
  console.log(`Got response from ${endpoint}`, doc, targetExtraction, schema, responseJSON);
  return responseJSON['node'] as PatternNode.t;
}
