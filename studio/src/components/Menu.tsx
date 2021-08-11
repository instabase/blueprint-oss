import React from 'react';
import './Menu.css';

export type Props = {
  rows: Row[];
  onActionExecute: () => void;
};

export default function Menu(props: Props) {
  return (
    <div className="Menu _belowParent">
      {props.rows.map((row) => (
        <Row
          key={row.text}
          row={row}
          onActionExecute={props.onActionExecute}
        />
      ))}
    </div>
  );
}

type ActionRow = {
  type: 'ActionRow';
  text: string;
  disabled?: boolean;
  action: () => void;
};

type SubmenuRow = {
  type: 'SubmenuRow';
  text: string;
  submenu: Props;
}

type DividerRow = {
  type: 'DividerRow';
};

type Row =
  | ActionRow
  // | SubmenuRow
  // | DividerRow
;

type RowProps = {
  row: Row;
  onActionExecute: () => void;
};

function Row(props: RowProps) {
  const classNames = ["_Row"];

  let onClick = (event: React.MouseEvent) => {};
  if (!props.row.disabled && props.row.action) {
    onClick = (event: React.MouseEvent) => {
      event.stopPropagation();
      event.preventDefault();
      props.row.action();
      props.onActionExecute();
    };
  } else {
    classNames.push("_disabled");
  }

  return (
    <div
      className={classNames.join(' ')}
      onClick={onClick}
    >
      {props.row.text}
    </div>
  );
}
