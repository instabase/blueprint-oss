import * as Date from 'studio/foundation/date';
import * as DollarAmount from 'studio/foundation/dollarAmount';
import * as Text from 'studio/foundation/text';

export const Types = [
  'Date',
  'DollarAmount',
  'Text',
] as const;

export type t =
  | Date.t
  | DollarAmount.t
  | Text.t
;

export type Type = typeof Types[number];

export const DefaultType: Type = 'Text';

export function text(entity: t): string | undefined {
  return entity.text;
}

export function heuristicDefaultType(field: string): Type {
  if (field.endsWith('date')) {
    return 'Date';
  } else if (field.endsWith('amount')) {
    return 'DollarAmount';
  } else if (field.endsWith('label') ||
             field.endsWith('anchor'))
  {
    return 'Text';
  } else {
    return 'Text';
  }
}

export function heuristicDefaultIsLabel(field: string): boolean {
  return heuristicDefaultType(field) == 'Text' &&
         (field.includes('label') ||
          field.includes('anchor'));
}
