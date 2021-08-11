import memo from 'memoizee';

import * as Entity from 'studio/foundation/entity';
import * as Doc from 'studio/foundation/doc';
import * as TargetWord from 'studio/foundation/targetWord';
import * as Word from 'studio/foundation/word';
import * as BBox from 'studio/foundation/bbox';
import * as Interval from 'studio/foundation/interval';

import assert from 'studio/util/assert';
import {NonemptyArray, isNonemptyArray} from 'studio/util/types';

export type t = {
  text: string | undefined;
  words: NonemptyArray<TargetWord.t> | undefined;
  geometry_validated: boolean;
};

export type NonNullTargetValue = {
  text: string;
  words: NonemptyArray<TargetWord.t> | undefined;
  geometry_validated: boolean;
};

export type PositionedTargetValue = {
  text: string;
  words: NonemptyArray<TargetWord.t>;
  geometry_validated: boolean;
};

export const NotPresent: t = {
  text: undefined,
  words: undefined,
  geometry_validated: true,
};

export function build(words: TargetWord.t[]): t {
  if (isNonemptyArray(words)) {
    words.sort(
      (w1: TargetWord.t, w2: TargetWord.t) =>
        w1.bbox.iy.a - w2.bbox.iy.a);

    type Line = TargetWord.t[];
    const initial: Line[] = [];
    const lines = words.reduce(
      (acc: Line[], word: TargetWord.t) => {
        if (isNonemptyArray(acc)) {
          const lastRow = acc[acc.length - 1];
          const gap = word.bbox.iy.a - lastRow[0].bbox.iy.a;
          if (gap > 0.5 * BBox.height(lastRow[0].bbox)) {
            const newRow: Line = [word];
            acc.push(newRow);
          } else {
            lastRow.push(word);
          }
          return acc;
        } else {
          return [[word]];
        }
      },
      initial);

    const ltrComparator =
      (w1: TargetWord.t, w2: TargetWord.t) => w1.bbox.ix.a - w2.bbox.ix.a;
    lines.forEach(line => line.sort(ltrComparator));

    const text = lines
      .map(row => row.map(word => word.text).join(' '))
      .join('\n');
    return {
      text,
      words: lines.flat() as NonemptyArray<TargetWord.t>,
      geometry_validated: true,
    };
  } else {
    return {
      text: undefined,
      words: undefined,
      geometry_validated: true,
    };
  }
}

export const bbox = memo(
  function(targetValue: PositionedTargetValue): BBox.t {
    return BBox.union(
      targetValue.words.map(word => word.bbox) as NonemptyArray<BBox.t>
    );
  }
);

export function approximateFromUserDragSelection(
  words: NonemptyArray<Entity.t>, doc: Doc.t): t | undefined
{
  return build(words.map(word => hack(word, doc)));
}

function hack(word: Entity.t, doc: Doc.t): TargetWord.t {
  return {
    text: word.text,
    bbox: BBox.percentageBasedPositionIn(word.bbox, doc.bbox),
  };
}

function approximatelyEqual(
  word1: TargetWord.t,
  word2: TargetWord.t):
    boolean
{
  const b1 = word1.bbox;
  const b2 = word2.bbox;

  const epsilon = 0.05 * Math.min(BBox.width(b1), BBox.height(b1),
                                  BBox.width(b2), BBox.height(b2));

  return Interval.approximatelyEqual(b1.ix, b2.ix, epsilon) &&
         Interval.approximatelyEqual(b1.iy, b2.iy, epsilon);
}

export function symmetricDifference(
  value1: t | undefined,
  value2: t | undefined):
    t | undefined
{
  if (!value1 || !value1.words) {
    return value2;
  } else if (!value2 || !value2.words) {
    return value1;
  } else {
    const keepers: TargetWord.t[] = [];
    const value2Words = new Set<TargetWord.t>([...value2.words]);
    value1.words.forEach(word1 => {
      const nearlyEqualValue2Words: TargetWord.t[] = [];
      value2Words.forEach(word2 => {
        if (approximatelyEqual(word1, word2)) {
          nearlyEqualValue2Words.push(word2);
        }
      });
      if (nearlyEqualValue2Words.length > 0) {
        nearlyEqualValue2Words.forEach(word2 => {
          value2Words.delete(word2);
        });
      } else {
        keepers.push(word1);
      }
    });
    return build(keepers.concat([...value2Words]));
  }
}

export function extractedValueShouldBeDefined(targetValue: t): boolean {
  return targetValue.text != undefined;
}

export function extractedValueShouldBeUndefined(targetValue: t): boolean {
  return targetValue.text == undefined;
}

export function isNonNull(targetValue: t): targetValue is NonNullTargetValue {
  return targetValue.text != undefined;
}

export function isPositioned(targetValue: t): targetValue is PositionedTargetValue {
  return isNonNull(targetValue) &&
         targetValue.words != undefined;
}

export function merged(existing: t, provided: t | undefined): t {
  // Erm. What's the right way to do this merge?
  return existing;
}
