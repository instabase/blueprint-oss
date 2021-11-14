import React from 'react';
import ActionContext from 'studio/context/ActionContext';
import {Trash2, XOctagon} from 'studio/components/StockSVGs';

import * as DocTargets from 'studio/foundation/docTargets';
import * as TargetValue from 'studio/foundation/targetValue';

type Props = {
  docName: string;
  field: string;
  value: TargetValue.t | undefined;
  isSelected: boolean;
};

export default function TargetValueCell(props: Props) {
  const actionContext = React.useContext(ActionContext);

  const Text = () => {
    if (props.value == undefined) {
      return <span className="MutedText SlightlySmallText">(unknown)</span>;
    } else if (props.value.text == undefined) {
      return <span className="MutedText SlightlySmallText">(null)</span>;
    } else if (props.value.text == '') {
      return <span className="MutedText SlightlySmallText">(empty string)</span>;
    } else {
      return <span className="EntityText">{props.value.text}</span>;
    }
  };

  return (
    <div className="TableView_Cell HiddenButtonsContainer">
      <div className="TableView_Cell_Contents">
        <Text />
      </div>

      <div className="HiddenButtons">
        <button
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              actionContext.dispatchAction({
                type: 'SetTargetValue',
                docName: props.docName,
                field: props.field,
                value: TargetValue.NotPresent,
              });
            }
          }
        >
          <XOctagon/>
        </button>
        <button
          onClick={
            event => {
              event.stopPropagation();
              event.preventDefault();
              actionContext.dispatchAction({
                type: 'SetTargetValue',
                docName: props.docName,
                field: props.field,
                value: undefined,
              });
            }
          }
        >
          <Trash2/>
        </button>
      </div>
    </div>
  );
}
