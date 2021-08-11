import React from 'react';
import ModalContext from 'studio/context/ModalContext';
import useKeyboardShortcut, {EscapeKey} from 'studio/hooks/useKeyboardShortcut';
import 'studio/components/AppModalBackdrop.css';

type Props = {
  children?: React.ReactNode;
  onCloseRequested?: () => 'AllowClose' | 'DontAllowClose';
};

export default function AppModalBackdrop(props: Props) {
  const modalContext = React.useContext(ModalContext);

  const close = React.useCallback(() => {
    modalContext.dispatchModalAction({
      name: 'AskModalToClose',
    });
  }, []);

  useKeyboardShortcut(EscapeKey, close);

  React.useEffect(() => {
    const cb = props.onCloseRequested;
    if (cb != undefined) {
      modalContext.dispatchModalAction({
        name: 'RegisterCloseRequestedCB',
        closeRequestedCB: cb,
      });
    }
  }, [modalContext, props.onCloseRequested]);

  return <div
    className="AppModalBackdrop"
    onClick={
      event => {
        // console.log('Modal backdrop clicked');
        event.stopPropagation();
        event.preventDefault();
        modalContext.dispatchModalAction({name: 'AskModalToClose'});
      }
    }
  >
    {props.children}
  </div>;
}
