import React from 'react';
import * as AutosaverState from 'studio/state/autosaverState';

type Props = {
  state: Readonly<AutosaverState.t>;
};

export default function AutosaverText(props: Props) {
  return <div
    style={{
      alignSelf: 'center',
      marginLeft: 'auto',
      fontSize: 'var(--small-font-size)',
      color: 'var(--slightly-muted-color)',
    }}
  >
    {text(props.state)}
  </div>;
}

function text(state: Readonly<AutosaverState.t>): string {
  let parts: string[] = [];

  if (state.lastSaveResult?.status == 'SaveProjectFailed') {
    parts.push(`(Error while autosaving, will retry: ${state.lastSaveResult.errorMessage})`);
  } else if (state.lastSaveResult) {
    parts.push(`Last saved at ${state.lastSaveResult.timestamp.toLocaleString()}.`);
  }

  if (state.projectBeingSaved) {
    parts.push('Saving...');
  }

  return parts.join(' ');
}
