import * as BBox from 'studio/foundation/bbox';
import * as Text from 'studio/foundation/text';

export type t = {
  bbox: BBox.t;

  text: string;
  words: Text.t[];
  likeness_score: number | undefined;
  type: 'DollarAmount';
};
