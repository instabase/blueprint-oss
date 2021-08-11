import React from 'react';
import * as Resource from 'studio/state/resource';
import useTriggerUpdate from 'studio/hooks/useTriggerUpdate';

export default function useResource<T>(promise: Promise<T> | undefined) {
  const lastPromiseRef = React.useRef<Promise<T> | undefined>(undefined);
  const resultRef = React.useRef<Resource.t<T>>({ status: 'NotAvailable' });
  const triggerUpdate = useTriggerUpdate();

  if (promise != undefined) {
    promise.catch(
      e => {
        // To avoid "Uncaught error in promise" from the browser.
      }
    );
  }

  if (lastPromiseRef.current != promise) {
    lastPromiseRef.current = promise;

    if (promise == undefined) {
      resultRef.current = { status: 'NotAvailable' };
    } else {
      resultRef.current = {
        status: 'Loading',
        promise,
      };

      promise.then(
        t => {
          if (promise == lastPromiseRef.current) {
            resultRef.current = {
              status: 'Done',
              value: t,
            };
            triggerUpdate();
          }
        }
      ).catch(
        e => {
          if (promise == lastPromiseRef.current) {
            resultRef.current = {
              status: 'Failed',
              errorCode: -1,
              errorMessage: e.toString(),
            };
            triggerUpdate();
          }
        }
      );
    }
  }

  return resultRef.current;
}
