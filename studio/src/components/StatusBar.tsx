import React from 'react';
import AutosaverText from 'studio/components/AutosaverText';
import * as AutosaverState from 'studio/state/autosaverState';
import 'studio/components/StatusBar.css';

type Props = {
  autosaverState: AutosaverState.t;
};

export default function StatusBar(props: Props) {
  return (
    <div className="StatusBar">
      <AutosaverText
        state={props.autosaverState}
      />
    </div>
  );
}
