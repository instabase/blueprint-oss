export type t =
  | 'NotUnderDragSelection'
  | 'UnderDragSelection'
;

export type Setter = (state: t) => void;
