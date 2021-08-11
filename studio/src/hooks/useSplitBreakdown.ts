import React from 'react';
import * as SplitBreakdown from 'studio/util/splitBreakdown';
import useLocalStorageState from 'studio/hooks/useLocalStorageState';
import {isObject} from 'studio/util/types';

export default function useSplitBreakdown(localStorageKey: string,
                                          defaultValue: SplitBreakdown.t)
{
  const validator = React.useCallback(
    (savedValue: unknown): savedValue is SplitBreakdown.t => {
      return isObject(savedValue) &&
             SplitBreakdown.isSplitBreakdown(savedValue, defaultValue.length);
    },
    [defaultValue]);

  let [breakdown, setBreakdown] =
    useLocalStorageState(localStorageKey, defaultValue, validator);

  return {breakdown, setBreakdown};
}
