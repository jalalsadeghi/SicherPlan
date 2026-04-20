<script setup lang="ts">
import { watch } from 'vue';

import { $t } from '@vben/locales';
import {
  FONT_SIZE_DEFAULT,
  FONT_SIZE_MAX,
  FONT_SIZE_MIN,
  FONT_SIZE_STEP,
} from '@vben/preferences';

import {
  NumberField,
  NumberFieldContent,
  NumberFieldDecrement,
  NumberFieldIncrement,
  NumberFieldInput,
} from '@vben-core/shadcn-ui';

defineOptions({
  name: 'PreferenceFontSize',
});

const modelValue = defineModel<number>({
  default: FONT_SIZE_DEFAULT,
});

const min = FONT_SIZE_MIN;
const max = FONT_SIZE_MAX;
const step = FONT_SIZE_STEP;

// 限制输入值在 min 和 max 之间
watch(
  modelValue,
  (newValue) => {
    if (newValue < min) {
      modelValue.value = min;
    } else if (newValue > max) {
      modelValue.value = max;
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="flex w-full flex-col gap-4">
    <div class="flex items-center gap-2">
      <NumberField
        v-model="modelValue"
        :max="max"
        :min="min"
        :step="step"
        class="w-full"
      >
        <NumberFieldContent>
          <NumberFieldDecrement />
          <NumberFieldInput />
          <NumberFieldIncrement />
        </NumberFieldContent>
      </NumberField>
      <span class="text-xs whitespace-nowrap text-muted-foreground">px</span>
    </div>
    <div class="text-xs text-muted-foreground">
      {{ $t('preferences.theme.fontSizeTip') }}
    </div>
  </div>
</template>
