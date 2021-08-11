import React from 'react';
import ProgressWidget, {Props as WidgetProps} from 'studio/components/ProgressWidget';

type Props = {
  widgetProps: Array<WidgetProps>;
};

export default function ProgressStack(props: Props) {
  return (
    <div
      style={{
        position: 'absolute',
        left: 'var(--medium-gutter)',
        bottom: 'var(--medium-gutter)',
        display: 'grid',
        gridTemplateColumns: 'min-content',
        gridGap: 'var(--small-gutter)',
      }}
    >
      {props.widgetProps.map(
        widgetProps => (
          <ProgressWidget
            key={widgetProps.taskUUID}
            {...widgetProps}
          />
        )
      )}
    </div>
  );
}
