import React from 'react';
import {useSpanRef} from 'studio/hooks/useDOMRef';

export type Props = {
  checked: boolean;
  disabled?: boolean;
  setChecked: (newValue: boolean) => void;
  tabIndex?: number;
};

export default function Checkbox(props: Props) {
  const ref = useSpanRef();
  React.useLayoutEffect(() => {
    const current = ref.current;
    if (current) {
      const checkbox = document.createElement('input');
      const focused = current.contains(document.activeElement);
      checkbox.type = 'checkbox';
      checkbox.checked = props.checked;
      if (props.tabIndex != undefined) {
        checkbox.tabIndex = props.tabIndex;
      }
      checkbox.disabled = Boolean(props.disabled);
      checkbox.onmousedown = (event) => event.stopPropagation();
      checkbox.onclick = (event) => {
        event.stopPropagation();
        props.setChecked(checkbox.checked);
      };
      (current as any).replaceChildren(checkbox); // XXX.
      if (focused) {
        checkbox.focus();
      }
    }
  });
  return <span ref={ref} />
}
