import { useEffect, useRef } from 'react';

const FOCUSABLE = 'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])';

/**
 * Keyboard behaviour a modal dialog needs: focus moves in when it opens, Tab stays inside, Escape closes,
 * and focus goes back to what opened it. Attach the returned ref to the dialog (or a wrapper around it).
 */
export function useDialogA11y(open: boolean, onClose: () => void) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  useEffect(() => {
    closeRef.current = onClose;
  });

  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    // Only elements that are actually shown: a responsive dialog may render a hidden twin
    const visible = () =>
      Array.from(ref.current?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []).filter((el) => el.getClientRects().length > 0);

    visible()[0]?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeRef.current();
        return;
      }
      if (e.key !== 'Tab') return;
      const items = visible();
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      const inside = ref.current?.contains(document.activeElement);
      if (!inside || (e.shiftKey && document.activeElement === first)) {
        e.preventDefault();
        (e.shiftKey ? last : first).focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      opener?.focus?.();
    };
  }, [open]);

  return ref;
}
