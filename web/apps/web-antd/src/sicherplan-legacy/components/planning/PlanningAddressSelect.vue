<template>
  <div class="planning-address-select field-stack" :class="wrapperClass">
    <span>{{ label }}</span>
    <Select
      :value="modelValue || undefined"
      show-search
      allow-clear
      :disabled="disabled"
      :loading="loading"
      :placeholder="resolvedPlaceholder"
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
  </div>
</template>

<script setup>
import { computed } from "vue";

import { Select } from "ant-design-vue";

import { formatPlanningAddressOption } from "@/features/planning/planningAdmin.helpers.js";

const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  customerId: {
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
  error: {
    type: String,
    default: "",
  },
  searchPlaceholder: {
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
  customerRequiredText: {
    type: String,
    required: true,
  },
  noMatchText: {
    type: String,
    required: true,
  },
  wrapperClass: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["update:modelValue"]);

const selectOptions = computed(() =>
  props.options.map((addressLink) => ({
    label: formatPlanningAddressOption(addressLink),
    value: addressLink.address_id,
  })),
);

const selectedOptionLabel = computed(
  () => selectOptions.value.find((option) => option.value === props.modelValue)?.label ?? "",
);

const resolvedPlaceholder = computed(() => {
  if (!props.customerId) {
    return props.customerRequiredText;
  }
  if (!props.loading && !props.error && !props.options.length) {
    return props.emptyText;
  }
  return props.searchPlaceholder;
});

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
.planning-address-select {
  min-width: 0;
}
</style>
