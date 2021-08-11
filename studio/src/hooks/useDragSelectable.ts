import {useContext, useEffect, useRef, useState} from 'react';
import * as State from 'studio/state/dragSelection';
import DragSelectionContext, {isCorrectlyTyped}
  from 'studio/context/DragSelectionContext';
import {useDivRef} from 'studio/hooks/useDOMRef';

export default function<T>(t: T): [React.RefObject<HTMLDivElement>, State.t] {
  const context = useContext(DragSelectionContext);
  const ref = useDivRef();
  const [state, setState] = useState<State.t>('NotUnderDragSelection');
  useEffect(() => {
    const current = ref.current;
    if (context != undefined && current != undefined &&
        isCorrectlyTyped<T>(context)) {
      context.register(current, t, setState);
      return () => context.unregister(current);
    }
  }, [t, context, ref.current]);
  return [ref, state];
}
