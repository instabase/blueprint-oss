import React from 'react';
import * as BBox from 'studio/foundation/bbox';
import BBoxView from 'studio/components/ImagePane/BBoxView';
import {useDivRef} from 'studio/hooks/useDOMRef';
import {startDrag} from 'studio/util/drag';
import * as DragSelectionState from 'studio/state/dragSelection';
import DragSelectionContext from 'studio/context/DragSelectionContext';
import 'studio/components/DragSelectionArea.css';

type Props<T> = {
  children: React.ReactNode;
  enabled: boolean;
  onSetSelection: (ts: T[]) => void;
  onToggleSelection: (ts: T[]) => void;
};

function DragSelectionArea<T>(props: Props<T>) {
  const [dragState, setDragState] =
    React.useState<State<T> | undefined>(undefined);
  const [elements] = React.useState<Elements<T>>(new Map());
  const clickableAreaRef = useDivRef();
  const contextValue = React.useMemo(() => ({
    register: (element: HTMLDivElement, t: T, setState: DragSelectionState.Setter) => {
      console.assert(!elements.has(element));
      elements.set(element, [t, setState]);
    },
    unregister: (element: HTMLDivElement) => {
      console.assert(elements.has(element));
      elements.delete(element);
    },
  }), [elements]);
  return (
    <DragSelectionContext.Provider value={contextValue} >
      <div
        className={
          'DragSelectionArea' +

          // This probably would not be necessary, and could be deleted,
          // if we captured all pointer events while dragging at the app level
          // (as we should).
          (dragState != undefined ? ' _dragging' : '')
        }
        ref={clickableAreaRef}
        onMouseDown={(startEvent: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
          startEvent.persist();

          const clickableArea = clickableAreaRef.current;
          if (!clickableArea || !props.enabled) {
            return;
          }

          const clickableAreaBBox = clientBBox(clickableArea);
          const x0 = startEvent.clientX;
          const y0 = startEvent.clientY;
          const p0 = {x: x0, y: y0};

          const getNewDragState = (dx: number, dy: number) => {
            const p = {x: x0 + dx, y: y0 + dy};
            const bbox = BBox.containing([p0, p]);
            const currentSelection = getCurrentSelection(elements, bbox);
            return {bbox, clickableAreaBBox, currentSelection};
          };

          let lastDragState = getNewDragState(0, 0);

          const internalSetDragState = (newDragState: State<T>) => {
            lastDragState = newDragState;
            setDragState(newDragState);
          };

          const onHaveMoved = (dx: number, dy: number) => {
            const newDragState = getNewDragState(dx, dy);
            internalSetDragState(newDragState);
          };

          const onFinished = () => {
            if (startEvent.metaKey) {
              props.onToggleSelection(lastDragState.currentSelection);
            } else {
              props.onSetSelection(lastDragState.currentSelection);
            }

            setDragState(undefined);
          };

          startDrag({startEvent, onHaveMoved, onFinished});
        }}
      >
        {props.children}

        {dragState &&
          <BBoxView
            className="DragSelectionRectangle"
            bbox={dragState.bbox}
            docBBox={dragState.clickableAreaBBox}
          />
        }
      </div>
    </DragSelectionContext.Provider>
  );
}

export default DragSelectionArea;

type State<T> = {
  bbox: BBox.t;
  clickableAreaBBox: BBox.t;
  currentSelection: T[];
};

type Elements<T> = Map<HTMLDivElement, [T, DragSelectionState.Setter]>;

function clientBBox(e: HTMLDivElement): BBox.t {
  const rect = e.getBoundingClientRect();
  return {
    ix: {a: rect.x, b: rect.x + rect.width},
    iy: {a: rect.y, b: rect.y + rect.height},
  };
}

function getCurrentSelection<T>(
  elements: Elements<T>,
  selectionClientBBox: BBox.t):
    T[]
{
  // console.log('Really iterating over everything');
  const result: T[] = [];
  for (const [element, [t, setState]] of elements.entries()) {
    if (BBox.intersect(clientBBox(element), selectionClientBBox)) {
      result.push(t);
    }
  }
  return result;
}
