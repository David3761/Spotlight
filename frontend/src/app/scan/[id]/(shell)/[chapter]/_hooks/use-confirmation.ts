import { useCallback, useEffect, useRef, useState } from "react";

/** How long a confirmation label such as „Copiat” stays on screen. */
const CONFIRMATION_DURATION_MS = 2200;

/** Tracks a short-lived "done" flag for button labels that confirm an action. */
export function useConfirmation() {
  const [isConfirmed, setIsConfirmed] = useState(false);
  const timerRef = useRef(0);

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  /** Turns the flag on and back off after the confirmation duration. */
  const confirm = useCallback(() => {
    window.clearTimeout(timerRef.current);
    setIsConfirmed(true);
    timerRef.current = window.setTimeout(() => setIsConfirmed(false), CONFIRMATION_DURATION_MS);
  }, []);

  return { isConfirmed, confirm };
}
