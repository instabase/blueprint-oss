import React from 'react';

export default function useTriggerUpdate() {
  const [_, updateState] =
    React.useState<{}>({});

  const updateScheduledRef = React.useRef<boolean>(false);
  updateScheduledRef.current = false;

  const triggerUpdate =
    React.useCallback(
      () => {
        if (!updateScheduledRef.current) {
          updateScheduledRef.current = true;
          updateState({});
        }
      }, [updateScheduledRef, updateState]);

  return triggerUpdate;
}
