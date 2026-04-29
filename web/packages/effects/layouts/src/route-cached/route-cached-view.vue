<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, unref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { preferences } from '@vben/preferences';
import { getTabKey, storeToRefs, useTabbarStore } from '@vben/stores';

import { useLayoutHook } from '../hooks';

import CachedRouteRenderer from './cached-route-renderer.vue';
import {
  getRouteCacheScrollTarget,
  readRouteCacheScrollTop,
} from './route-cache-scroll';
import RouteCachePane from './route-cache-pane.vue';
import {
  cleanupMissingRouteCacheSessions,
  restoreRouteCacheSessionScrollPosition,
  saveRouteCacheSessionScrollPosition,
} from './route-cache-session';

const route = useRoute();

const tabbarStore = useTabbarStore();

const { getTabs, getCachedRoutes, getExcludeCachedTabs } =
  storeToRefs(tabbarStore);
const { removeCachedRoute } = tabbarStore;

const { getEnabledTransition, getTransitionName } = useLayoutHook();

/**
 * 是否启用tab
 */
const enableTabbar = computed(() => preferences.tabbar.enable);

const computedCachedRouteKeys = computed(() => {
  if (!unref(enableTabbar)) {
    return [];
  }
  return unref(getTabs)
    .filter((item) => item.meta.domCached)
    .map((item) => getTabKey(item));
});

/**
 * 所有缓存的route
 */
const computedCachedRoutes = computed(() => {
  if (!unref(enableTabbar)) {
    return [];
  }
  // 刷新路由可刷新缓存
  const excludeCachedTabKeys = unref(getExcludeCachedTabs);
  return [...unref(getCachedRoutes).values()].filter((item) => {
    const componentType: any = item.component.type || {};
    let componentName = componentType.name;
    if (!componentName) {
      componentName = item.route.name;
    }
    return !excludeCachedTabKeys.includes(componentName);
  });
});

/**
 * 是否显示
 */
const computedShowView = computed(() => unref(computedCachedRoutes).length > 0);

const computedCurrentRouteKey = computed(() => {
  return getTabKey(route);
});

let activeScrollTarget: HTMLElement | null = null;
let pendingRestoreFrame: number | null = null;
let pendingSaveFrame: number | null = null;

function cancelPendingRestore() {
  if (pendingRestoreFrame !== null) {
    window.cancelAnimationFrame(pendingRestoreFrame);
    pendingRestoreFrame = null;
  }
}

function cancelPendingSave() {
  if (pendingSaveFrame !== null) {
    window.cancelAnimationFrame(pendingSaveFrame);
    pendingSaveFrame = null;
  }
}

function detachScrollListener() {
  activeScrollTarget?.removeEventListener('scroll', handleActiveScroll);
  activeScrollTarget = null;
}

function attachScrollListener() {
  const nextTarget = getRouteCacheScrollTarget(document);
  if (activeScrollTarget === nextTarget) {
    return;
  }
  detachScrollListener();
  activeScrollTarget = nextTarget;
  activeScrollTarget.addEventListener('scroll', handleActiveScroll, {
    passive: true,
  });
}

function saveScrollPosition(key = unref(computedCurrentRouteKey)) {
  if (!key) {
    return;
  }
  saveRouteCacheSessionScrollPosition(key, readRouteCacheScrollTop(document));
}

function restoreScrollPosition(key: string) {
  restoreRouteCacheSessionScrollPosition(key, document);
}

function scheduleRestoreScrollPosition(key: string) {
  cancelPendingRestore();
  attachScrollListener();
  restoreScrollPosition(key);
  void nextTick(() => {
    pendingRestoreFrame = -1;
    const frameId = window.requestAnimationFrame(() => {
      pendingRestoreFrame = null;
      if (unref(computedCurrentRouteKey) !== key) {
        return;
      }
      attachScrollListener();
      restoreScrollPosition(key);
    });
    if (pendingRestoreFrame !== null) {
      pendingRestoreFrame = frameId;
    }
  });
}

function handleActiveScroll() {
  if (pendingSaveFrame !== null) {
    return;
  }
  pendingSaveFrame = -1;
  const frameId = window.requestAnimationFrame(() => {
    pendingSaveFrame = null;
    saveScrollPosition();
  });
  if (pendingSaveFrame !== null) {
    pendingSaveFrame = frameId;
  }
}

watch(
  computedCurrentRouteKey,
  (key, previousKey) => {
    if (previousKey) {
      saveScrollPosition(previousKey);
    }
    if (key) {
      scheduleRestoreScrollPosition(key);
    }
  },
  { flush: 'sync', immediate: true },
);

watch(computedCachedRouteKeys, (keys) => {
  cleanupMissingRouteCacheSessions(keys);
  for (const item of unref(getCachedRoutes).values()) {
    if (!keys.includes(item.key)) {
      removeCachedRoute(item.key);
    }
  }
});

onBeforeUnmount(() => {
  cancelPendingRestore();
  cancelPendingSave();
  detachScrollListener();
});
</script>

<template>
  <template v-if="computedShowView">
    <template v-for="item in computedCachedRoutes" :key="item.key">
      <RouteCachePane
        :active="item.key === computedCurrentRouteKey"
        :cache-key="item.key"
        :route="item.route"
      >
        <Transition
          v-if="getEnabledTransition"
          appear
          mode="out-in"
          :name="getTransitionName(item.route)"
        >
          <CachedRouteRenderer
            :cache-key="item.key"
            :component="item.component"
            :route="item.route"
          />
        </Transition>
        <template v-else>
          <CachedRouteRenderer
            :cache-key="item.key"
            :component="item.component"
            :route="item.route"
          />
        </template>
      </RouteCachePane>
    </template>
  </template>
</template>

<style scoped></style>
