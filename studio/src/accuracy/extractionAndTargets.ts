import * as RecordTargets from 'studio/foundation/recordTargets';
import * as Extraction from 'studio/foundation/extraction';

import {Nonempty, isEmptyArray} from 'studio/util/types';

export type t = [
  Extraction.t | undefined,
  RecordTargets.t | undefined,
];

export type PopulatedExtractionAndTargets = [
  Extraction.t,
  RecordTargets.t,
];

export function isPopulated(pair: t):
  pair is PopulatedExtractionAndTargets
{
  return pair[0] != undefined && pair[1] != undefined;
}
