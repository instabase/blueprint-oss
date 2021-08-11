export function hasOwnProperty<X extends {}, Y extends PropertyKey>
  (obj: X, prop: Y): obj is X & Record<Y, unknown>
{
  return obj.hasOwnProperty(prop);
}

export type UUID = string;

export function isBoolean(x: unknown): x is boolean {
  return typeof x == 'boolean';
}

export function isString(x: unknown): x is string {
  return typeof x == 'string';
}

export function isArray<T>(x: unknown, validator: (y: unknown) => y is T): x is Array<T> {
  return Array.isArray(x) && x.every(y => validator(y));
}

export function isStringArray(x: unknown): x is string[] {
  return isArray<string>(x, isString);
}

export function isObject(x: unknown): x is object {
  return typeof x == 'object';
}

export function isNumber(x: unknown): x is number {
  return typeof x == 'number';
}

export function isNonnegativeNumber(x: unknown): boolean {
  return isNumber(x) && x >= 0;
}

export type Nonempty<T> =
  T extends Array<infer U> ? U[] & {'0': U} : never;

export type NonemptyArray<T> = Nonempty<T[]>;

export function isNonemptyArray<T>(x: T[]): x is Nonempty<T[]> {
  return x.length > 0;
}

export function isEmptyArray<T>(x: T[]): x is [] {
  return x.length == 0;
}

export function isNotUndefined<T>(t: T | undefined): t is T {
  return t != undefined;
}
