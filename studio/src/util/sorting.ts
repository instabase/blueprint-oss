export function booleanSort<T>(getter: (t: T) => boolean | undefined) {
  return (t1: T, t2: T): number => {
    const val1 = getter(t1);
    const val2 = getter(t2);
    if (val1 == undefined || val2 == undefined) {
      if (val1 != undefined && val2 == undefined) {
        return -1;
      } else if (val1 == undefined && val2 != undefined) {
        return 1;
      } else {
        return 0;
      }
    } else if (val1 && !val2) {
      return -1;
    } else if (val2 && !val1) {
      return 1;
    } else {
      return 0;
    }
  }
}

export function numericalSort<T>(getter: (t: T) => number | undefined) {
  return (t1: T, t2: T): number => {
    const val1 = getter(t1);
    const val2 = getter(t2);
    if (val1 == undefined || val2 == undefined) {
      if (val1 != undefined && val2 == undefined) {
        return -1;
      } else if (val1 == undefined && val2 != undefined) {
        return 1;
      } else {
        return 0;
      }
    } else if (val1 < val2) {
      return -1;
    } else if (val1 > val2) {
      return 1;
    } else {
      return 0;
    }
  }
}

export function reversedNumericalSort<T>(getter: (t: T) => number | undefined) {
  return (t1: T, t2: T): number => {
    const val1 = getter(t1);
    const val2 = getter(t2);
    if (val1 == undefined || val2 == undefined) {
      if (val1 != undefined && val2 == undefined) {
        return -1;
      } else if (val1 == undefined && val2 != undefined) {
        return 1;
      } else {
        return 0;
      }
    } else if (val1 < val2) {
      return 1;
    } else if (val1 > val2) {
      return -1;
    } else {
      return 0;
    }
  }
}

export function stringSort<T>(getter: (t: T) => string | undefined) {
  return (t1: T, t2: T): number => {
    const val1 = getter(t1);
    const val2 = getter(t2);
    if (val1 == undefined || val2 == undefined) {
      if (val1 != undefined && val2 == undefined) {
        return -1;
      } else if (val1 == undefined && val2 != undefined) {
        return 1;
      } else {
        return 0;
      }
    } else if (val1 < val2) {
      return -1;
    } else if (val2 > val1) {
      return 1;
    } else {
      return 0;
    }
  }
}
