import useLocalStorageState from 'studio/hooks/useLocalStorageState';

import {isStringArray} from 'studio/util/types';

const KEY = 'Studio.RecentProjectPaths-v1';

export default function() {
  return useLocalStorageState<string[]>(
    KEY,
    [],
    isStringArray);
}

export function clear() {
  localStorage.removeItem(KEY);
  window.location.reload();
}
