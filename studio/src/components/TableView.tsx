import React from 'react';

import * as Interval from 'studio/foundation/interval';

import useLocalStorageState from 'studio/hooks/useLocalStorageState';
import useSplitBreakdown from 'studio/hooks/useSplitBreakdown';
import {useAnchorRef, useDivRef} from 'studio/hooks/useDOMRef';
import useKeyboardShortcut, {Shortcut} from 'studio/hooks/useKeyboardShortcut';

import assert from 'studio/util/assert';
import * as SplitBreakdown from 'studio/util/splitBreakdown';
import {hasOwnProperty, isBoolean, isObject, isNumber, isString} from 'studio/util/types';

import {ControlledSplit} from 'studio/components/Split';

import 'studio/components/TableView.css';

export type Spec<T> = {
  columns: ColumnSpec<T>[];
  localStorageSuffix: string;
  rowID: (t: T) => string;
  rowIsSelected?: (t: T) => boolean;
  hasChildren?: (t: T) => boolean;
  getChildren?: (t: T) => T[];
  childIsSelected?: (t: T) => boolean;

  // WARNING: prevRow and nextRow only work for flat (non-tree) table views.
  onRowSelected?: (
    t: T,
    parents: T[],
    prevRow: T | undefined,
    nextRow: T | undefined,
  ) => void;

  rowClassName?: (t: T) => string;
  rowChildren?: (t: T) => React.ReactNode;
  rowsCollapsedByDefault?: boolean;

  // WARNING: These only work for flat (non-tree) table views.
  prevRowKeyboardShortcut?: Shortcut;
  nextRowKeyboardShortcut?: Shortcut;
};

type ColumnSpec<T> = {
  name: string;
  element?: JSX.Element;
  footer?: JSX.Element;
  fractionalWidth: number;
  hiddenByDefault?: boolean;
  cellContents: (t: T, expanded: boolean) => JSX.Element | string | undefined;
  comparisonFunction: (t1: T, t2: T) => number;
};

type Props<T> = {
  spec: Spec<T>;
  rootRows: Readonly<T[]>;

  // These should be positioned.
  // This is mainly for CornerButtons.
  children?: React.ReactNode;
};

export default function TableView<T>(props: Props<T>) {
  const hidden = (column: ColumnSpec<T>): boolean => {
    return column.hiddenByDefault == true;
  };

  const fractionalWidths =
    props.spec.columns.map(
      column =>
        !hidden(column) ?
          column.fractionalWidth :
          undefined);

  const defaultBreakdown = React.useMemo(
    () => fractionalWidths.filter(isNumber),
    [fractionalWidths.length, ...fractionalWidths],
  );

  const {breakdown, setBreakdown} = useSplitBreakdown(
    `Studio.TableView.SplitBreakdown-v1-${props.spec.localStorageSuffix}`,
    defaultBreakdown);

  const defaultSortSettings = React.useMemo(
    () => ({
      columnName: props.spec.columns[0].name,
      reversed: false,
    }), [props.spec.columns[0]?.name]
  );

  const isValidSortSettings = React.useCallback(
    function isSortSettings(o: any): o is SortSettings {
      return isObject(o) &&
        hasOwnProperty(o, 'columnName') &&
        isString(o.columnName) &&
        props.spec.columns.some(column => column.name == o.columnName) &&
        hasOwnProperty(o, 'reversed') &&
        isBoolean(o.reversed);
    }, [props.spec.columns]
  );

  const [sortSettings, setSortSettings] = useLocalStorageState(
    `Studio.TableView.SortSettings-v1-${props.spec.localStorageSuffix}`,
    defaultSortSettings,
    isValidSortSettings,
  );

  const sortedRows: T[] =
    props.rootRows
      .concat()
      .sort(sortComparisonFunction(props.spec, sortSettings));

  const useKeyboardShortcuts =
    props.spec.prevRowKeyboardShortcut != undefined ||
    props.spec.nextRowKeyboardShortcut != undefined;

  const selectedRowIndex = sortedRows.findIndex(
    row => props.spec.rowIsSelected && props.spec.rowIsSelected(row)
  );

  const selectPrevRow = React.useCallback(
    () => {
      const prevRow =
        getPrevRow(sortedRows, selectedRowIndex) ||
        sortedRows[0];
      if (prevRow) {
        actualRowSelected(
          props.spec,
          prevRow,
          /* parents = */ [],
          getPrevRow(sortedRows, selectedRowIndex - 1),
          getNextRow(sortedRows, selectedRowIndex - 1),
        );
      }
    },
    [
      useKeyboardShortcuts && props.spec,
      useKeyboardShortcuts && selectedRowIndex,
      useKeyboardShortcuts && sortedRows,
    ],
  );

  const selectNextRow = React.useCallback(
    () => {
      const nextRow =
        getNextRow(sortedRows, selectedRowIndex) ||
        sortedRows[0];
      if (nextRow) {
        actualRowSelected(
          props.spec,
          nextRow,
          /* parents = */ [],
          getPrevRow(sortedRows, selectedRowIndex + 1),
          getNextRow(sortedRows, selectedRowIndex + 1),
        );
      }
    },
    [
      useKeyboardShortcuts && props.spec,
      useKeyboardShortcuts && selectedRowIndex,
      useKeyboardShortcuts && sortedRows,
    ],
  );

  useKeyboardShortcut(
    props.spec.prevRowKeyboardShortcut,
    selectPrevRow,
  );

  useKeyboardShortcut(
    props.spec.nextRowKeyboardShortcut,
    selectNextRow,
  );

  return <div className="TableView">
    <ControlledSplit
      className="_header"
      dir={SplitBreakdown.Direction.Vertical}
      breakdown={breakdown}
      setBreakdown={setBreakdown}
      dragbarSize={0}
    >
      {visibleColumns(props.spec).map(column =>
        <React.Fragment key={column.name}>
          {
            (column.element && column.element) ||
            <div
              className="TableView_Header"
              onClick={
                event => {
                  event.stopPropagation();
                  event.preventDefault();
                  if (sortSettings.columnName == column.name) {
                    setSortSettings({
                      ...sortSettings,
                      reversed: !sortSettings.reversed,
                    });
                  } else {
                    setSortSettings({
                      columnName: column.name,
                      reversed: false,
                    });
                  }
                }
              }
            >
              {column.name == sortSettings.columnName &&
                <span style={{
                  fontSize: '5pt',
                  verticalAlign: 'center',
                  position: 'relative',
                  bottom: '2px',
                }}>
                  {sortSettings.reversed ? '▲' : '▼'}&nbsp;
                </span>
              }
              {column.name}
            </div>
          }
        </React.Fragment>
      )}
    </ControlledSplit>

    <div className="_body">
      {[...sortedRows.keys()].map(
        index => {
          const row = sortedRows[index];
          const prevRow =
            props.spec.hasChildren != undefined ?
              undefined : getPrevRow(sortedRows, index);
          const nextRow =
            props.spec.hasChildren != undefined ?
              undefined : getNextRow(sortedRows, index);
          return (
            <Row
              key={props.spec.rowID(row)}
              t={row}
              parents={[]}
              spec={props.spec}
              breakdown={breakdown}
              sortSettings={sortSettings}
              prevRow={prevRow}
              nextRow={nextRow}
            />
          );
        }
      )}

      <div className="_row _gutter" />
    </div>

    {hasFooter(props.spec) &&
      <ControlledSplit
        className="_footer"
        dir={SplitBreakdown.Direction.Vertical}
        breakdown={breakdown}
        setBreakdown={setBreakdown}
        dragbarSize={0}
      >
        {visibleColumns(props.spec).map(column =>
          <React.Fragment key={column.name}>
            {
              (column.footer && column.footer) ||
              <div className="TableView_Footer" />
            }
          </React.Fragment>
        )}
      </ControlledSplit>
    }

    {props.children}
  </div>;
}

// Rows
// ====

type RowProps<T> = {
  t: T;
  parents: T[];
  spec: Spec<T>;
  breakdown: SplitBreakdown.t;
  sortSettings: SortSettings;

  // In sort order.
  prevRow: T | undefined;
  nextRow: T | undefined;
};

function Row<T>(props: RowProps<T>) {
  const spec = props.spec;

  const [isExpanded, setIsExpanded] = useLocalStorageState(
    `Studio.TableView.IsExpanded-v1-${spec.localStorageSuffix}-${spec.rowID(props.t)}`,
    !spec.rowsCollapsedByDefault,
    isBoolean);

  const hasChildren =
    callIfDefined(spec.hasChildren, props.t, false);

  const onToggleExpanded =
    hasChildren ? () => setIsExpanded(!isExpanded) : undefined;

  const visibleChildren = () =>
    hasChildren
      ? callIfDefined(spec.getChildren, props.t, [])
      : [];

  const selected =
    callIfDefined(spec.rowIsSelected, props.t, false);

  const latestPropsRef =
    React.useRef<RowProps<T>>(props);
  latestPropsRef.current = props;

  return <>
    <a
      href="javascript: ;"
      className={
        'FakeAnchor ' +
        '_row' +
        (selected ? ' _selected' : '') +
        (spec.rowClassName ? ' ' + spec.rowClassName(props.t) : '')
      }
      style={
        SplitBreakdown.gridStyle(
          SplitBreakdown.Direction.Vertical,
          props.breakdown
        )
      }
      onClick={
        event => {
          rowSelected(props);
        }
      }
    >
      {
        visibleColumns(props.spec).map(
          (column, index) => (
            <Cell
              key={column.name}
              rowProps={props}
              column={column}
              isLeftmostColumn={index == 0}
              isExpanded={isExpanded}
              onToggleExpanded={onToggleExpanded}
            />
          )
        )
      }

      {
        spec.rowChildren != undefined &&
        spec.rowChildren(props.t)
      }
    </a>

    {
      isExpanded &&
      visibleChildren()
      .concat()
      .sort(sortComparisonFunction(spec, props.sortSettings))
      .map((child: T) =>
        <Row
          key={spec.rowID(child)}
          t={child}
          parents={props.parents.concat([props.t])}
          spec={spec}
          breakdown={props.breakdown}
          sortSettings={props.sortSettings}

          prevRow={undefined}
          nextRow={undefined}
        />
      )
    }
  </>;
};

// Cells
// =====

type CellProps<T> = {
  rowProps: RowProps<T>;
  column: ColumnSpec<T>;
  isLeftmostColumn: boolean;
  isExpanded: boolean; // Only used for rows with children.
  onToggleExpanded: (() => void) | undefined;
};

function Cell<T>(props: CellProps<T>) {
  if (canHaveTriangles(props.rowProps.spec) &&
      props.isLeftmostColumn)
  {
    return <TriangleCell {...props} />;
  } else {
    return <CellContents {...props} />;
  }
}

function TriangleCell<T>(props: CellProps<T>) {
  return <div className="_triangleCell">
    <Triangle {...props} />
    <CellContents {...props} />
  </div>;
}

function Triangle<T>(props: CellProps<T>) {
  const hasChildren = callIfDefined(
    props.rowProps.spec.hasChildren,
    props.rowProps.t,
    false);

  return <div
    className={
      '_triangle' +
      (hasChildren ? '' : ' _invisible')
    }
    style={{marginLeft: `${8 + 20 * props.rowProps.parents.length}px`}}
    onClick={event => {
      event.stopPropagation();
      event.preventDefault();
      props.onToggleExpanded && props.onToggleExpanded();
    }}
  >
    {props.isExpanded ? '▼' : '▶'}
  </div>
}

function CellContents<T>(props: CellProps<T>) {
  const result = props.column.cellContents(props.rowProps.t, props.isExpanded);
  if (isString(result) || result == undefined) {
    return (
      <div className="TableView_Cell">
        <div className="TableView_Cell_Contents">
          {result}
        </div>
      </div>
    );
  } else {
    return result;
  }
}

// Sorting
// =======

type SortSettings = {
  columnName: string;
  reversed: boolean;
};

function sortComparisonFunction<T>(
  spec: Spec<T>,
  sortSettings: SortSettings,
) {
  const column = spec.columns.find(
    column => column.name == sortSettings.columnName);

  if (column == undefined) {
    throw 'Invalid sort settings';
  }

  return (t1: T, t2: T) => {
    if (sortSettings.reversed) {
      return column.comparisonFunction(t2, t1);
    } else {
      return column.comparisonFunction(t1, t2);
    }
  };
}

// Other
// =====

function hasFooter<T>(spec: Spec<T>) {
  return spec.columns.some(
    column => column.footer != undefined);
}

function canHaveTriangles<T>(spec: Spec<T>) {
  return spec.hasChildren != undefined;
}

function visibleColumns<T>(spec: Spec<T>) {
  return spec.columns.filter(column => !column.hiddenByDefault);
}

function call<X, Y>(f: ((x: X, y: Y) => void) | undefined, x: X, y: Y) {
  if (f) f(x, y);
}

function callIfDefined<X, Y>(f: ((x: X) => Y) | undefined, x: X, y0: Y): Y {
  return f ? f(x) : y0;
}

function getPrevRow<T>(rows: T[], index: number) {
  if (index != -1) {
    return rows[(index + rows.length - 1) % rows.length];
  }
}

function getNextRow<T>(rows: T[], index: number) {
  if (index != -1) {
    return rows[(index + rows.length + 1) % rows.length];
  }
}

function rowSelected<T>(rowProps: RowProps<T>) {
  if (rowProps.spec.onRowSelected) {
    actualRowSelected(
      rowProps.spec,
      rowProps.t,
      rowProps.parents,
      rowProps.prevRow,
      rowProps.nextRow,
    );
  }
}

function actualRowSelected<T>(
  spec: Spec<T>,
  row: T,
  parents: T[],
  prevRow: T | undefined,
  nextRow: T | undefined)
{
  if (spec.onRowSelected) {
    spec.onRowSelected(
      row,
      parents,
      prevRow,
      nextRow,
    );
  }
}
