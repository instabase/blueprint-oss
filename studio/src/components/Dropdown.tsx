import React from 'react';
import 'studio/components/Dropdown.css';

export type Props<T> = {
  options: readonly T[];
  selected: T | undefined;
  stringify: (t: T) => string;
  onSelected: (t: T) => void;

  className?: string;
  tabIndex?: number;
};

export default function<T>(props: Props<T>) {
  const stringToT = new Map<string, T>();
  props.options.forEach(t => {
    const s = props.stringify(t);
    if (stringToT.has(s)) {
      throw 'Duplicate string value in dropdown: ' + s;
    }
    stringToT.set(s, t);
  });

  return (
    <select
      className={
        'Dropdown' +
        (props.className ? ' ' + props.className : '')
      }
      disabled={props.options.length == 0}
      onChange={(event) => {
        props.onSelected(
          stringToT.get(
            event.target.value) as T)
      }}
      value={props.selected ? props.stringify(props.selected) : undefined}
      tabIndex={props.tabIndex != undefined ? props.tabIndex : 0}
      onMouseDown={event => event.stopPropagation()}
      onClick={event => event.stopPropagation()}
    >
      {props.options.map(props.stringify).map(s =>
        <option
          key={s}
          value={s}
        >
          {s}
        </option>
      )}
    </select>
  );
}
