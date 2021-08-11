import React from 'react';
import {useDivRef} from 'studio/hooks/useDOMRef';
import FocusTrap from 'focus-trap-react';
import 'studio/components/Dialog.css';

type Props = {
  width?: number;
  height?: number;
  children: React.ReactNode;
  focusTrapDisabled?: boolean;
};

export default function Dialog(props: Props) {
  const ref = useDivRef();
  React.useEffect(() => {
    if (ref.current) {
      ref.current.focus();
    }
  }, [ref.current]);
  return (
    <FocusTrap
      active={!props.focusTrapDisabled}
      focusTrapOptions={{
        escapeDeactivates: false,
        allowOutsideClick: true,
      }}
    >
      <div
        ref={ref}
        className="Dialog"
        style={{
          width: props.width,
          height: props.height,
        }}
        onClick={event => {
          event.preventDefault();
          event.stopPropagation();
        }}
      >
        <div className="_contents">
          {props.children}
        </div>
      </div>
    </FocusTrap>
  );
}
