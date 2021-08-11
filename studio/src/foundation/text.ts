import * as BBox from 'studio/foundation/bbox';
import * as Word from 'studio/foundation/word';

export type t = {
  bbox: BBox.t;

  text: string;
  words: Word.t[];
  maximality_score: number | undefined;
  ocr_score: number | undefined;
  type: 'Text';
};
