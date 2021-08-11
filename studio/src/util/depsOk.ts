// AFAIK this is how React does deps comparison.
export default function depsOk(deps1: unknown[], deps2: unknown[]): boolean {
  if (deps1.length != deps2.length) {
    return false;
  } else {
    for (let i = 0; i < deps1.length; ++i) {
      if (deps1[i] != deps2[i]) {
        return false;
      }
    }

    return true;
  }
}
