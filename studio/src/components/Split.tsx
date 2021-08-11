import React from 'react';
import * as SplitBreakdown from 'studio/util/splitBreakdown';
import useSplitBreakdown from 'studio/hooks/useSplitBreakdown';
import {useDivRef} from 'studio/hooks/useDOMRef';
import {startDrag} from 'studio/util/drag';
import 'studio/components/Split.css';

type Props = {
  localStorageSuffix: string;
  children: JSX.Element[];
  defaultBreakdown?: SplitBreakdown.t;
};

export function Column(props: Props) {
  const {children, ...childProps} = props;
  return (
    <Split {...childProps} dir={SplitBreakdown.Direction.Horizontal}>
      {children}
    </Split>
  );
}

export function Row(props: Props) {
  const {children, ...childProps} = props;
  return (
    <Split {...childProps} dir={SplitBreakdown.Direction.Vertical}>
      {children}
    </Split>
  );
}

type SplitProps = {
  localStorageSuffix: string;
  children: JSX.Element[];
  dir: SplitBreakdown.Direction;
  defaultBreakdown?: SplitBreakdown.t;
};

const Split = ({localStorageSuffix, children, dir, defaultBreakdown}: SplitProps) => {
  defaultBreakdown = React.useMemo(() => {
    if (defaultBreakdown) {
      return defaultBreakdown;
    } else {
      return Array(children.length).fill(1);
    }
  }, [defaultBreakdown, children.length]);

  let {breakdown, setBreakdown} = useSplitBreakdown(
    `Studio.Split.Breakdown-v1-${localStorageSuffix}`,
    defaultBreakdown,
  );

  return (
    <ControlledSplit
      dir={dir}
      breakdown={breakdown}
      setBreakdown={setBreakdown}
    >
      {children}
    </ControlledSplit>
  );
};

type ControlledSplitOptionalProps = {
  className: string;
  dragbarSize: number;
};

type ControlledSplitProps = {
  children: JSX.Element[];
  dir: SplitBreakdown.Direction;
  breakdown: SplitBreakdown.t;
  setBreakdown: (breakdown: SplitBreakdown.t) => void;
} & Partial<ControlledSplitOptionalProps>;

const DefaultOptionalValues: ControlledSplitOptionalProps = {
  className: '',
  dragbarSize: 1,
};

export function ControlledSplit(partialProps: ControlledSplitProps) {
  const container = useDivRef();

  const props = {...DefaultOptionalValues, ...partialProps};
  const childrenWithDragBars = [];
  for (let childNum = 0; childNum < props.children.length; ++childNum) {
    if (childNum != 0) {
      childrenWithDragBars.push(
        <DragBar
          key={2*childNum - 1}
          startDrag={(event: React.MouseEvent) => {
            startDragResize(
              props.dragbarSize,
              props.dir,
              event,
              container.current,
              props.breakdown,
              childNum - 1,
              props.setBreakdown);
          }}
        />
      );
    }
    childrenWithDragBars.push(
      <React.Fragment key={2*childNum}>
        {props.children[childNum]}
      </React.Fragment>
    );
  }

  return (
    <div
      ref={container}
      className={containerClassName[props.dir] + ' ' + props.className}
      style={SplitBreakdown.gridStyle(
        props.dir, props.breakdown, props.dragbarSize)}
    >
      {childrenWithDragBars}
    </div>
  );
}

type DragBarProps = {
  startDrag: (e: React.MouseEvent) => void;
};

const DragBar = (props: DragBarProps) => {
  return (
    <div className="_dragbar">
      <div
        className="_grabbable"
        onMouseDown={props.startDrag}
      />
    </div>
  );
};

function startDragResize(
  dragbarSize: number,
  splitDirection: SplitBreakdown.Direction,
  startEvent: React.MouseEvent,
  container: HTMLElement,
  originalBreakdown: SplitBreakdown.t,
  firstIndex: number,
  setBreakdown: (breakdown: SplitBreakdown.t) => void,
) {
  const secondIndex = firstIndex + 1;
  const numChildren = originalBreakdown.length;
  if (!(0 <= firstIndex && firstIndex < numChildren) ||
      !(0 <= secondIndex && secondIndex < numChildren)) {
    throw 'Invalid arguments to startDragResize';
  }

  const rect = container.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  const size = splitDirection == SplitBreakdown.Direction.Vertical ? width : height;

  const sizeWithoutDragbars = size - numChildren * dragbarSize;

  const totalFRWeight = originalBreakdown.reduce((a, b) => a + b, 0);
  const frUnitsPerPixel = totalFRWeight / sizeWithoutDragbars;

  const breakdown = (displacement: number) => {
    const result = [...originalBreakdown];

    let frUnitsDisplacement = displacement * frUnitsPerPixel;
    if (-frUnitsDisplacement > originalBreakdown[firstIndex]) {
      frUnitsDisplacement = -originalBreakdown[firstIndex];
    }
    if (frUnitsDisplacement > originalBreakdown[secondIndex]) {
      frUnitsDisplacement = originalBreakdown[secondIndex];
    }

    result[firstIndex] += frUnitsDisplacement;
    result[secondIndex] -= frUnitsDisplacement;

    return result;
  };

  return startDrag({
    startEvent,
    onHaveMoved: (dx: number, dy: number) => {
      const displacement = splitDirection == SplitBreakdown.Direction.Vertical ? dx : dy;
      setBreakdown(breakdown(displacement));
    },
  });
}

const containerClassName = {
  [SplitBreakdown.Direction.Horizontal]: 'Split _horizontal',
  [SplitBreakdown.Direction.Vertical]: 'Split _vertical',
};
