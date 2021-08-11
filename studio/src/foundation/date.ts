import * as BBox from 'studio/foundation/bbox';
import * as Word from 'studio/foundation/word';

export type t = {
  bbox: BBox.t;

  text: string;
  words: Word.t[];
  likeness_score: number | undefined;
  type: 'Date';
};
