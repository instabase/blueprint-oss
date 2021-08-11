import {hasOwnProperty, isObject, isNumber} from 'studio/util/types';

export type t = Readonly<{
  scale: number;
  x: number;
  y: number;
}>;

export function isZoomAndPanTransform(t: unknown): t is t {
  return isObject(t) &&
         hasOwnProperty(t, 'scale') && isNumber(t.scale) &&
         hasOwnProperty(t, 'x') && isNumber(t.x) &&
         hasOwnProperty(t, 'y') && isNumber(t.y);
}

export function zoomedBy(original: t, wheelMotion: number, x0: number, y0: number): t {
  const boundedWheelMotion = Math.min(Math.max(-20, wheelMotion), 20);
  const scaleFactor = 1 + boundedWheelMotion / 400;
  const scale = Math.max(0.03, Math.min(original.scale * scaleFactor, 5));
  const appliedScaleFactor = scale / original.scale;
  const x = original.x + (original.x - x0) * (appliedScaleFactor - 1);
  const y = original.y + (original.y - y0) * (appliedScaleFactor - 1);
  return {scale, x, y};
}

export function translatedBy(original: t, dx: number, dy: number): t {
  return {
    ...original,
    x: original.x + dx,
    y: original.y + dy,
  };
}
