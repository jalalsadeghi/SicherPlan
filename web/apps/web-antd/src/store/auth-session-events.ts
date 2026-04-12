const listeners = new Set<() => void>();

export function emitAuthSessionStateChanged() {
  for (const listener of listeners) {
    try {
      listener();
    } catch {
      // Session scheduling must not break login/refresh/logout flows.
    }
  }
}

export function subscribeAuthSessionStateChanged(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
