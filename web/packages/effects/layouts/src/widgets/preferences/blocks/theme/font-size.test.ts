import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import FontSize from './font-size.vue';

vi.mock('@vben/locales', () => ({
  $t: (key: string) => key,
}));

vi.mock('@vben/preferences', () => ({
  FONT_SIZE_DEFAULT: 14,
  FONT_SIZE_MAX: 22,
  FONT_SIZE_MIN: 12,
  FONT_SIZE_STEP: 1,
}));

vi.mock('@vben-core/shadcn-ui', async () => {
  const { defineComponent, h } = await import('vue');

  const passthrough = (name: string) =>
    defineComponent({
      name,
      setup(_, { slots }) {
        return () => h('div', { 'data-testid': name }, slots.default?.());
      },
    });

  const NumberField = defineComponent({
    name: 'NumberField',
    props: {
      max: { type: Number, required: true },
      min: { type: Number, required: true },
      modelValue: { type: Number, required: false, default: undefined },
      step: { type: Number, required: true },
    },
    emits: ['update:modelValue'],
    setup(props, { emit, slots }) {
      return () =>
        h(
          'div',
          {
            'data-max': String(props.max),
            'data-min': String(props.min),
            'data-model-value': String(props.modelValue),
            'data-step': String(props.step),
            'data-testid': 'number-field',
            onSetValue: (event: CustomEvent<number>) => emit('update:modelValue', event.detail),
          },
          slots.default?.(),
        );
    },
  });

  return {
    NumberField,
    NumberFieldContent: passthrough('NumberFieldContent'),
    NumberFieldDecrement: passthrough('NumberFieldDecrement'),
    NumberFieldIncrement: passthrough('NumberFieldIncrement'),
    NumberFieldInput: passthrough('NumberFieldInput'),
  };
});

describe('PreferenceFontSize', () => {
  it('uses min 12, max 22, step 1, and default model 14', () => {
    const wrapper = mount(FontSize);
    const field = wrapper.get('[data-testid="number-field"]');

    expect(field.attributes('data-min')).toBe('12');
    expect(field.attributes('data-max')).toBe('22');
    expect(field.attributes('data-step')).toBe('1');
    expect(field.attributes('data-model-value')).toBe('14');
  });

  it('clamps values below 12 to 12', async () => {
    const wrapper = mount(FontSize);
    const numberField = wrapper.getComponent({ name: 'NumberField' });

    numberField.vm.$emit('update:modelValue', 11);
    await nextTick();

    expect(wrapper.get('[data-testid="number-field"]').attributes('data-model-value')).toBe('12');
  });

  it('clamps values above 22 to 22', async () => {
    const wrapper = mount(FontSize);
    const numberField = wrapper.getComponent({ name: 'NumberField' });

    numberField.vm.$emit('update:modelValue', 23);
    await nextTick();

    expect(wrapper.get('[data-testid="number-field"]').attributes('data-model-value')).toBe('22');
  });
});
