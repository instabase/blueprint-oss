import {isNonnegativeNumber, isObject} from 'studio/util/types';

export enum Direction {
  Horizontal,
  Vertical,
}

export type t = number[];

export function isSplitBreakdown(o: object, numChildren: number): o is t {
  return Array.isArray(o) &&
         o.every((n) => isNonnegativeNumber(n)) &&
         o.length == numChildren;
}

function appendFR(n: number) {
  return `${n}fr`;
}

const styleKey = {
  [Direction.Horizontal]: 'gridTemplateRows',
  [Direction.Vertical]: 'gridTemplateColumns',
};

export function gridStyle(dir: Direction,
                          breakdown: t,
                          interstitialElementSize?: number)
{
  const separator = interstitialElementSize != undefined ? ` ${interstitialElementSize}px ` : ' ';
  return {
    [styleKey[dir]]: breakdown.map(appendFR).join(separator),
  };
}

export const Breakdown_1_1 = [1, 1];
export const Breakdown_1_2 = [1, 2];
export const Breakdown_1_1_2 = [1, 1, 2];
export const Breakdown_1_3 = [1, 3];
export const Breakdown_2_1 = [2, 1];
export const Breakdown_2_1_1 = [2, 1, 1];
export const Breakdown_3_1 = [3, 1];
export const Breakdown_4_1_3 = [4, 1, 3];
