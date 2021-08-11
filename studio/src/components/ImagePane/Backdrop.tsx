import React, {useEffect, useRef} from 'react';
import {useDivRef} from 'studio/hooks/useDOMRef';
import {startDrag} from 'studio/util/drag';
import * as Transform from 'studio/util/zoomAndPanTransform';
import './Backdrop.css';

type Props = {
  children: JSX.Element;
  transform: Transform.t;
  setTransform: (transform: Transform.t) => void;
};

export default function Backdrop(props: Props) {
  const backdrop = useDivRef();

  const transformRef = useRef<Transform.t>(props.transform);
  transformRef.current = props.transform;
  useEffect(() => {
    const backdropElement = backdrop.current;
    const setTransform = props.setTransform;
    const onWheel = (event: WheelEvent) => {
      wheelZoom(event, backdropElement, transformRef, setTransform);
    };
    backdropElement.addEventListener('wheel', onWheel, {passive: false});
    return () => {
      backdropElement.removeEventListener('wheel', onWheel);
    };
  }, [
    backdrop.current,
    props.setTransform,
  ]);

  const onMouseDown = (event: React.MouseEvent) => {
    mousePan(event, props.transform, props.setTransform);
  };

  return (
    <div
      ref={backdrop}
      className="DocImageBackdrop"
      onMouseDown={onMouseDown}
    >
      {props.children}
    </div>
  );
}

function wheelZoom(event: WheelEvent,
                   backdrop: HTMLElement,
                   transformRef: React.MutableRefObject<Transform.t>,
                   setTransform: (t: Transform.t) => void)
{
  event.preventDefault();
  event.stopPropagation();

  if (event.metaKey) {
    setTransform(
      Transform.translatedBy(
        transformRef.current, -event.deltaX, -event.deltaY));
  } else {
    const rect = backdrop.getBoundingClientRect();
    const x0 = event.pageX - (rect.left + rect.right) / 2;
    const y0 = event.pageY - (rect.top + rect.bottom) / 2;
    setTransform(
      Transform.zoomedBy(
        transformRef.current,
        -event.deltaY, x0, y0));
  }
}

function mousePan(event: React.MouseEvent,
                  original: Transform.t,
                  setTransform: (t: Transform.t) => void)
{
  if (event.button == 0) { // Left mouse button.
    startDrag({
      startEvent: event,
      onHaveMoved: (dx: number, dy: number) => {
        setTransform(
          Transform.translatedBy(
            original, dx, dy));
      },
    });
  }
}
