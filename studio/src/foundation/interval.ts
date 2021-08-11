export type t = {
  a: number;
  b: number;
};

export function length(interval: t): number {
  return interval.b - interval.a;
}

export function intersect(i1: t, i2: t): boolean {
  return Math.max(i1.a, i2.a) <= Math.min(i1.b, i2.b);
}

export function intersection(i1: t, i2: t): t {
  return {
    a: Math.max(i1.a, i2.a),
    b: Math.min(i1.b, i2.b),
  };
}

export function contains(i1: t, i2: t): boolean {
  return i1.a <= i2.a && i2.b <= i1.b;
}

export function approximatelyEqual(i1: t, i2: t, epsilon: number) {
  return Math.abs(i1.a - i2.a) < epsilon &&
         Math.abs(i1.b - i2.b) < epsilon;
}

export function midpoint(i: t): number {
  return (i.a + i.b) / 2;
}

export function lowerHalf(i: t): t {
  return {a: i.a, b: midpoint(i)};
}

export function upperHalf(i: t): t {
  return {a: midpoint(i), b: i.b};
}

export function absoluteSubinterval(i: t, percentageInterval: t) {
  return {
    a: i.a + percentageInterval.a * length(i),
    b: i.a + percentageInterval.b * length(i),
  };
}
