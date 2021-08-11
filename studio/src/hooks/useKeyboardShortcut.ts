import React from 'react';

import ModalContext, {modalOpen} from 'studio/context/ModalContext';

export type Shortcut = {
  key: string;
  shiftKey?: boolean;
  altKey?: boolean;
  ctrlKey?: boolean;
  metaKey?: boolean;
};

export default function useKeyboardShortcut(
  shortcut: Shortcut | undefined,
  callback: (() => void) | undefined)
{
  const modalContext = React.useContext(ModalContext);

  React.useEffect(() => {
    if (shortcut && callback && !modalOpen(modalContext)) {
      const wrappedCallback = (event: KeyboardEvent) => {
        if (document.activeElement?.tagName?.toLowerCase() == 'input' ||
            document.activeElement?.tagName?.toLowerCase() == 'textarea')
        {
          return;
        }

        if (matches(event, shortcut)) {
          event.stopPropagation();
          event.preventDefault();
          callback();
        }
      };
      window.addEventListener('keydown', wrappedCallback);
      return () => window.removeEventListener('keydown', wrappedCallback);
    }
  }, [shortcut, callback, !modalOpen(modalContext)]);
}

function matches(event: KeyboardEvent, shortcut: Shortcut) {
  return event.key.toUpperCase() == shortcut.key.toUpperCase() &&
         event.shiftKey == Boolean(shortcut.shiftKey) &&
         event.altKey == Boolean(shortcut.altKey) &&
         event.ctrlKey == Boolean(shortcut.ctrlKey) &&
         event.metaKey == Boolean(shortcut.metaKey);
}

export const EscapeKey: Shortcut = {
  key: 'Escape',
};

export const TabKey: Shortcut = {
  key: 'Tab',
};

export const ShiftTabKey: Shortcut = {
  key: 'Tab',
  shiftKey: true,
};
