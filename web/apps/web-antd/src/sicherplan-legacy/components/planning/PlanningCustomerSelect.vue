<template>
  <div class="planning-customer-select field-stack">
    <span>{{ label }}</span>
    <Select
      :value="modelValue || undefined"
      show-search
      allow-clear
      :disabled="disabled"
      :loading="loading"
      :placeholder="searchPlaceholder"
      :filter-option="filterOption"
      :options="selectOptions"
      :status="error ? 'error' : undefined"
      popup-class-name="planning-admin-select-dropdown"
      class="planning-admin-select"
      @change="handleChange"
      @clear="handleClear"
    />

    <p v-if="loading" class="field-help">{{ loadingText }}</p>
    <p v-else-if="error" class="field-help">{{ error }}</p>
    <p v-else-if="!options.length" class="field-help">{{ emptyText }}</p>
    <p v-else-if="modelValue && !selectedOptionLabel" class="field-help">{{ noMatchText }}</p>
  </div>
</template>

<script setup>
import { computed } from "vue";

import { Select } from "ant-design-vue";

import {
  formatPlanningCustomerOption,
} from "@/features/planning/planningAdmin.helpers.js";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  label: {
    type: String,
    required: true,
  },
  options: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  searchPlaceholder: {
    type: String,
    required: true,
  },
  emptyOptionLabel: {
    type: String,
    required: true,
  },
  loadingText: {
    type: String,
    required: true,
  },
  emptyText: {
    type: String,
    required: true,
  },
  noMatchText: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue"]);

const selectOptions = computed(() =>
  props.options.map((customer) => ({
    label: formatPlanningCustomerOption(customer),
    value: customer.id,
  })),
);

const selectedOptionLabel = computed(
  () => selectOptions.value.find((option) => option.value === props.modelValue)?.label ?? "",
);

function filterOption(input, option) {
  if (!input) {
    return true;
  }
  const label = typeof option?.label === "string" ? option.label : "";
  return label.toLowerCase().includes(input.toLowerCase());
}

function handleChange(value) {
  emit("update:modelValue", typeof value === "string" ? value : "");
}

function handleClear() {
  emit("update:modelValue", "");
}
</script>

<style scoped>
.planning-customer-select {
  min-width: 0;
}
</style>
