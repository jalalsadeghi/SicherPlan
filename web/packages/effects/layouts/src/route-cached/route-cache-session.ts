import type { MaybeRefOrGetter } from 'vue';
import type { RouteLocationNormalizedLoadedGeneric } from 'vue-router';

import { computed, inject, toValue } from 'vue';

import {
  getRouteCacheScrollTarget,
  readRouteCacheScrollTop,
  writeRouteCacheScrollTop,
} from './route-cache-scroll';

export interface RouteCacheSession {
  readonly cacheKey: string;
  readonly isActive: boolean;
  readonly route: RouteLocationNormalizedLoadedGeneric;
  readonly scrollTarget: HTMLElement;
  canSync(): boolean;
  cleanup(): void;
  readScroll(): number;
  restoreScroll(): void;
  saveScroll(force?: boolean): void;
  writeScroll(scrollTop: number): void;
}

export const routeCacheSessionKey = Symbol('route-cache-session');

const routeCacheSessionScrollState = new Map<string, number>();

interface CreateRouteCacheSessionOptions {
  active: MaybeRefOrGetter<boolean>;
  cacheKey: MaybeRefOrGetter<string>;
  doc?: Document;
  route: MaybeRefOrGetter<RouteLocationNormalizedLoadedGeneric>;
}

export function createRouteCacheSession(
  options: CreateRouteCacheSessionOptions,
): RouteCacheSession {
  const doc = options.doc ?? document;

  const session: RouteCacheSession = {
    get cacheKey() {
      return toValue(options.cacheKey);
    },
    get isActive() {
      return toValue(options.active);
    },
    get route() {
      return toValue(options.route);
    },
    get scrollTarget() {
      return getRouteCacheScrollTarget(doc);
    },
    canSync() {
      return session.isActive;
    },
    cleanup() {
      if (!session.cacheKey) {
        return;
      }
      routeCacheSessionScrollState.delete(session.cacheKey);
    },
    readScroll() {
      return readRouteCacheScrollTop(doc);
    },
    restoreScroll() {
      if (!session.cacheKey) {
        return;
      }
      writeRouteCacheScrollTop(
        routeCacheSessionScrollState.get(session.cacheKey) ?? 0,
        doc,
      );
    },
    saveScroll(force = false) {
      if (!session.cacheKey || (!force && !session.canSync())) {
        return;
      }
      routeCacheSessionScrollState.set(session.cacheKey, session.readScroll());
    },
    writeScroll(scrollTop: number) {
      writeRouteCacheScrollTop(scrollTop, doc);
    },
  };

  return session;
}

export function cleanupMissingRouteCacheSessions(cacheKeys: Iterable<string>) {
  const activeKeys = new Set(cacheKeys);
  for (const key of [...routeCacheSessionScrollState.keys()]) {
    if (!activeKeys.has(key)) {
      routeCacheSessionScrollState.delete(key);
    }
  }
}

export function hasRouteCacheSessionState(cacheKey: string) {
  return routeCacheSessionScrollState.has(cacheKey);
}

export function saveRouteCacheSessionScrollPosition(
  cacheKey: string,
  scrollTop: number,
) {
  routeCacheSessionScrollState.set(cacheKey, scrollTop);
}

export function restoreRouteCacheSessionScrollPosition(
  cacheKey: string,
  doc: Document = document,
) {
  writeRouteCacheScrollTop(routeCacheSessionScrollState.get(cacheKey) ?? 0, doc);
}

export function resetRouteCacheSessionState() {
  routeCacheSessionScrollState.clear();
}

export function useRouteCacheSession() {
  return inject<RouteCacheSession | null>(routeCacheSessionKey, null);
}

export function useIsRouteCachePaneActive() {
  const session = useRouteCacheSession();
  return computed(() => session?.isActive ?? true);
}

export function useRouteCacheScrollTarget() {
  const session = useRouteCacheSession();
  return computed(
    () => session?.scrollTarget ?? getRouteCacheScrollTarget(document),
  );
}
