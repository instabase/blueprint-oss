import {UUID} from 'studio/util/types';
import {v4 as uuidv4} from 'uuid';

export const Names = [
  'text_equals',
  'bottom_aligned',
  'left_aligned',
  'right_aligned',
  'left_to_right',
  'top_down',
  'are_on_same_page',
  'nothing_between_horizontally',
  'nothing_between_vertically',
  'no_words_between_horizontally',
  'no_words_between_vertically',
] as const;

export type Name = typeof Names[number];

export type t = {
  uuid: UUID;
  name: Name;
} & (
  | TextEquals
  | BottomAligned
  | TopAligned
  | LeftAligned
  | RightAligned
  | LeftToRight
  | TopDown
  | AreOnSamePage
  | NothingBetweenHorizontally
  | NothingBetweenVertically
  | NoWordsBetweenHorizontally
  | NoWordsBetweenVertically
);

export type TextEquals = {
  name: 'text_equals';
  texts: string[];
  tolerance: number;
  taper: number;
};

export type BottomAligned = {
  name: 'bottom_aligned';
  tolerance: number;
  taper: number;
};

export type TopAligned = {
  name: 'top_aligned';
  tolerance: number;
  taper: number;
};

export type LeftAligned = {
  name: 'left_aligned';
  tolerance: number;
  taper: number;
};

export type RightAligned = {
  name: 'right_aligned';
  tolerance: number;
  taper: number;
};

export type LeftToRight = {
  name: 'left_to_right';
  taper: number;
};

export type TopDown = {
  name: 'top_down';
  taper: number;
};

export type AreOnSamePage = {
  name: 'are_on_same_page';
  tolerance: number;
  taper: number;
};

export type NothingBetweenHorizontally = {
  name: 'nothing_between_horizontally';
  maximum_impingement: number;
};

export type NothingBetweenVertically = {
  name: 'nothing_between_vertically';
  maximum_impingement: number;
};

export type NoWordsBetweenHorizontally = {
  name: 'no_words_between_horizontally';
  maximum_impingement: number;
};

export type NoWordsBetweenVertically = {
  name: 'no_words_between_vertically';
  maximum_impingement: number;
};

export function build(name: Name): t {
  switch (name) {
    case 'text_equals':
      return {
        uuid: uuidv4(),
        name,
        texts: [''],
        tolerance: 1,
        taper: 1,
      };
    case 'bottom_aligned':
      return {
        uuid: uuidv4(),
        name,
        tolerance: 0.5,
        taper: 0.5,
      };
    case 'left_aligned':
    case 'right_aligned':
      return {
        uuid: uuidv4(),
        name,
        tolerance: 1,
        taper: 1,
      };
    case 'left_to_right':
    case 'top_down':
      return {
        uuid: uuidv4(),
        name,
        taper: 0.5,
      };
    case 'nothing_between_horizontally':
    case 'nothing_between_vertically':
      return {
        uuid: uuidv4(),
        name,
        maximum_impingement: 1,
      };
    case 'no_words_between_horizontally':
    case 'no_words_between_vertically':
      return {
        uuid: uuidv4(),
        name,
        maximum_impingement: 0.5,
      };
  }
  return <never>0;
}

export function copy(predicate: t): t {
  return {
    ...predicate,
    uuid: uuidv4(),
  };
}

export function displayName(predicate: t): string {
  return predicate.name;
}
