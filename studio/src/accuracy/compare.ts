import memo from 'memoizee';

import * as RecordTargets from 'studio/foundation/recordTargets';
import * as Entity from 'studio/foundation/entity';
import * as Extraction from 'studio/foundation/extraction';
import * as TargetValue from 'studio/foundation/targetValue';

import {Nonempty, isEmptyArray} from 'studio/util/types';

import * as ExtractionAndTargets from 'studio/accuracy/extractionAndTargets';

export type MatchResult =
  | 'NoMatchResult'
  | 'PositiveMatchResult'
  | 'NegativeMatchResult'
;

export function toBoolean(matchResult: MatchResult): boolean | undefined {
  switch (matchResult) {
  case 'NoMatchResult':
    return undefined;
  case 'PositiveMatchResult':
    return true;
  case 'NegativeMatchResult':
    return false;
  }
}

export const match = memo(
  function(
    extractedValue: Entity.t | undefined,
    targetValue: TargetValue.t | undefined):
      MatchResult
  {
    if (targetValue == undefined ||
        targetValue.text == '') /* This is technically wrong. */
    {
      return 'NoMatchResult';
    } else if (extractedValue == undefined) {
      if (TargetValue.extractedValueShouldBeUndefined(targetValue)) {
        return 'PositiveMatchResult';
      } else {
        return 'NegativeMatchResult';
      }
    } else if (extractedValue.text == undefined ||
               targetValue.text == undefined)
    {
      return extractedValue.text == targetValue.text
        ? 'PositiveMatchResult'
        : 'NegativeMatchResult';
    } else {
      switch (extractedValue.type) {
      case 'Date':
      case 'Text':
        if (extractedValue.text == targetValue.text) {
          return 'PositiveMatchResult';
        } else {
          return 'NegativeMatchResult';
        }
      case 'DollarAmount':
        if (alphanumericLowerCase(extractedValue.text) ==
            alphanumericLowerCase(targetValue.text))
        {
          return 'PositiveMatchResult';
        } else {
          return 'NegativeMatchResult';
        }
      }
    }
  }
);

function ord(s: string): number {
  return s.charCodeAt(0);
}

function chr(charCode: number): string {
  return String.fromCharCode(charCode);
}

function alphanumericLowerCase(s: string): string {
  let result = '';
  for (let i = 0; i < s.length; ++i) {
    const c = s.charCodeAt(i);
    if (ord('0') <= c && c <= ord('9')) {
      result += chr(c);
    } else if (ord('a') <= c && c <= ord('z')) {
      result += chr(c);
    } else if (ord('A') <= c && c <= ord('Z')) {
      result += chr(ord('a') + c - ord('A'));
    }
  }
  return result;
}

export const FLA = memo(
  function(
    extraction: Extraction.t,
    recordTargets: RecordTargets.t,
    flaFields: string,
  ): number
  {
    // console.log('Computing FLA', extraction, recordTargets, flaFields);

    const pairs: [Entity.t | undefined, TargetValue.t][] =
      RecordTargets.fields(recordTargets).filter(
        field => flaFields.length == 0 || flaFields.includes(field)
      ).map(
        field => ([
          Extraction.value(extraction, field),
          RecordTargets.value(recordTargets, field) as TargetValue.t,
        ])
      );

    const results = pairs.map(
      ([extractedValue, targetValue]) => (
        match(extractedValue, targetValue)
      )
    );

    const numDefinitiveResults = results.filter(
      result => result != 'NoMatchResult').length;
    const numPositiveResults = results.filter(
      result => result == 'PositiveMatchResult').length;

    // console.log(
    //  'FLA comparison results',
    //  pairs,
    //  results,
    //  numDefinitiveResults,
    //  numPositiveResults,
    // ;

    if (numDefinitiveResults == 0) {
      return 1;
    } else {
      return numPositiveResults / numDefinitiveResults;
    }
  }
);

function sum(xs: number[]): number {
  return xs.reduce((acc: number, x: number) => acc + x, 0);
}

export function average(xs: Nonempty<number[]>): number {
  return sum(xs) / xs.length;
}

export const averageFLA = memo(
  function(
    pairs: ExtractionAndTargets.t[],
    flaFields: string,
  ): number | undefined
  {
    const populatedPairs =
      pairs.filter(
        ExtractionAndTargets.isPopulated);

    if (isEmptyArray(populatedPairs)) {
      return undefined;
    } else {
      return average(
        populatedPairs.map(
          ([extraction, targets]) => (
            FLA(extraction, targets, flaFields)
          )
        ) as Nonempty<number[]>
      );
    }
  }
);
