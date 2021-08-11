import React from 'react';

type DragProps = {
  startEvent: React.MouseEvent;
  onMove?: (dx: number, dy: number) => void;
  onHaveMoved?: (dx: number, dy: number) => void;
  onFinished?: () => void;
};

export function startDrag(props: DragProps) {
  const origin = {
    x: props.startEvent.pageX,
    y: props.startEvent.pageY,
  };
  
  const last = {...origin};

  const onMouseMove = (event: MouseEvent) => {
    event.stopPropagation();
    event.preventDefault();

    const x = event.pageX;
    const y = event.pageY;

    if (props.onMove) props.onMove(x - last.x, y - last.y);
    if (props.onHaveMoved) props.onHaveMoved(x - origin.x, y - origin.y);

    last.x = x;
    last.y = y;
  };

  const onMouseUp = () => {
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
    if (props.onFinished) props.onFinished();
  };

  props.startEvent.stopPropagation();
  props.startEvent.preventDefault();
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}
