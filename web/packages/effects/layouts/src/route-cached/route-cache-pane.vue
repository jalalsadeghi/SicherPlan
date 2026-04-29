<script setup lang="ts">
import type { RouteLocationNormalizedLoadedGeneric } from 'vue-router';

import { computed, onBeforeUnmount, provide, toRef } from 'vue';

import {
  createRouteCacheSession,
  routeCacheSessionKey,
} from './route-cache-session';

interface Props {
  active: boolean;
  cacheKey: string;
  route: RouteLocationNormalizedLoadedGeneric;
}

const props = defineProps<Props>();

const session = createRouteCacheSession({
  active: toRef(props, 'active'),
  cacheKey: toRef(props, 'cacheKey'),
  route: toRef(props, 'route'),
});

provide(routeCacheSessionKey, session);

const paneVisible = computed(() => props.active);

onBeforeUnmount(() => {
  session.cleanup();
});
</script>

<template>
  <div
    v-show="paneVisible"
    class="route-cache-pane size-full"
    :data-route-cache-key="cacheKey"
  >
    <slot />
  </div>
</template>
