import * as Interval from './interval';

test('intersection', () => {
  const I1: Interval.t = {a: 0, b: 1};
  const I2: Interval.t = {a: 2, b: 3};
  const I3: Interval.t = {a: 2.5, b: 3.5};
  expect(Interval.intersect(I1, I2)).toBe(false);
  expect(Interval.intersect(I1, I3)).toBe(false);
  expect(Interval.intersect(I2, I3)).toBe(true);
});
