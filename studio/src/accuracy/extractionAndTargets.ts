import * as DocTargets from 'studio/foundation/docTargets';
import * as Extraction from 'studio/foundation/extraction';

import {Nonempty, isEmptyArray} from 'studio/util/types';

export type t = [
  Extraction.t | undefined,
  DocTargets.t | undefined,
];

export type PopulatedExtractionAndTargets = [
  Extraction.t,
  DocTargets.t,
];

export function isPopulated(pair: t):
  pair is PopulatedExtractionAndTargets
{
  return pair[0] != undefined && pair[1] != undefined;
}
