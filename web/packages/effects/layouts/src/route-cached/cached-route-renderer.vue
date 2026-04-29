<script setup lang="ts">
import type { VNode } from 'vue';
import type { RouteLocationNormalizedLoadedGeneric } from 'vue-router';

import { cloneVNode, computed, provide, shallowReactive, watch } from 'vue';
import { routeLocationKey } from 'vue-router';

import { transformComponent } from '../hooks';

interface Props {
  cacheKey: string;
  component?: VNode;
  route: RouteLocationNormalizedLoadedGeneric;
}

const props = defineProps<Props>();

const localRoute = shallowReactive({
  ...props.route,
});

function syncLocalRoute(nextRoute: RouteLocationNormalizedLoadedGeneric) {
  for (const key of Object.keys(localRoute)) {
    if (!(key in nextRoute)) {
      delete (localRoute as Record<string, unknown>)[key];
    }
  }
  Object.assign(localRoute, nextRoute);
}

watch(
  () => props.route,
  (nextRoute) => {
    syncLocalRoute(nextRoute);
  },
  { immediate: true },
);

provide(routeLocationKey, localRoute);

const renderedComponent = computed(() => {
  if (!props.component) {
    return undefined;
  }
  const component = transformComponent(props.component, localRoute);
  if (!component) {
    return undefined;
  }
  return cloneVNode(component, { key: props.cacheKey });
});
</script>

<template>
  <component :is="renderedComponent" :key="cacheKey" />
</template>
