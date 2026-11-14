import { useSyncExternalStore } from "react";

/** The media query that matches the desktop layout. */
const DESKTOP_QUERY = "(min-width: 1024px)";

/** Subscribes `onChange` to changes of the desktop media query and returns the unsubscribe function. */
function subscribe(onChange: () => void): () => void {
  const list = window.matchMedia(DESKTOP_QUERY);
  list.addEventListener("change", onChange);
  return () => list.removeEventListener("change", onChange);
}

/** Returns whether the viewport is desktop-sized right now. */
function getSnapshot(): boolean {
  return window.matchMedia(DESKTOP_QUERY).matches;
}

/** Returns the desktop flag used during server rendering, where the mobile layout is assumed. */
function getServerSnapshot(): boolean {
  return false;
}

/** Returns `true` while the viewport is at least 1024 px wide. */
export function useIsDesktop(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
