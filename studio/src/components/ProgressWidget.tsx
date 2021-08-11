import React from 'react';
import {UUID} from 'studio/util/types';

export type Props = {
  taskUUID: UUID;
  numerator: number;
  denominator: number;
  onCancel: () => void;
};

export default function ProgressWidget(props: Props) {
  const {onCancel, ...progressBarProps} = props;
  return (
    <div 
      style={{
        background: 'var(--canvas-color)',
        fontSize: 'var(--small-font-size)',
        padding: 'var(--medium-gutter)',
        border: 'var(--default-border)',
        borderRadius: 'var(--medium-border-radius)',
        display: 'grid',
        gridTemplateColumns: 'min-content min-content',
        gridGap: 'var(--medium-gutter)'
      }}
    >
      <ProgressBar {...progressBarProps} />
      <button
        className="VerySmallText"
        style={{
          padding: 'var(--tiny-gutter) var(--small-gutter)',
        }}
        onClick={
          event => {
            event.stopPropagation()
            event.preventDefault();
            onCancel();
          }
        }
      >
        Cancel
      </button>
    </div>
  );
}

type ProgressBarProps = {
  numerator: number;
  denominator: number;
};

function ProgressBar(props: ProgressBarProps) {
  const width = 80;
  const percentage =  
    props.denominator != 0 ?
      props.numerator / props.denominator : 1;
  const hackNumber = 2;
  const progressWidth = percentage * width +
    (percentage > 0 ? 2 * hackNumber : 0); // Hack ... eh.

  return (
    <div
      style={{
        position: 'relative',
        width: '80px',
        background: 'black',
        borderRadius: 'var(--medium-border-radius)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          width: `${progressWidth}px`,
          left: `-${hackNumber}px`,
          height: `${100 + 2 * hackNumber}%`,
          top: `-${hackNumber}%`,
          background: 'var(--primary-color)',
        }}
      />
      <div
        className="VerySmallText CenterInParent NoWrap"
        style={{color: 'white'}}
      >
        {props.numerator} / {props.denominator}
      </div>
    </div>
  );
}
