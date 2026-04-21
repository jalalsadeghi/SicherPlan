<script lang="ts" setup>
import { computed } from 'vue';

import { Button, Card, Space } from 'ant-design-vue';

import SectionHeader from '#/components/sicherplan/section-header.vue';

interface CalendarSummaryItem {
  label: string;
  value: string;
}

interface CalendarCellItem {
  key: string;
  label: string;
  route?: string;
  tone: 'bad' | 'good' | 'warn';
  coverageStateLabel: string;
}

interface CalendarCell {
  dateKey: string;
  dayLabel: string;
  inMonth: boolean;
  isToday: boolean;
  visibleItems: CalendarCellItem[];
  moreCount: number;
  shiftCount: number;
  orderCount: number;
}

const props = defineProps<{
  actionLabel?: string;
  actionTo?: string;
  cells: CalendarCell[];
  description: string;
  loading?: boolean;
  loadingLabel?: string;
  monthHint: string;
  monthLabel: string;
  moreLabel: string;
  nextLabel: string;
  orderShortLabel: string;
  previousLabel: string;
  shiftShortLabel: string;
  summary: CalendarSummaryItem[];
  title: string;
  weekDayLabels: string[];
}>();

const emit = defineEmits<{
  shiftCalendar: [direction: 'next' | 'prev'];
  toggleDay: [dateKey: string];
}>();

const hasAction = computed(() => !!props.actionLabel && !!props.actionTo);

function shiftCalendar(direction: 'next' | 'prev') {
  emit('shiftCalendar', direction);
}

function toggleDay(dateKey: string) {
  emit('toggleDay', dateKey);
}
</script>

<template>
  <Card :bordered="false" class="sp-dashboard__calendar-card">
    <div class="sp-dashboard__panel-head">
      <SectionHeader :description="description" :title="title" />
      <Space wrap>
        <Button @click="shiftCalendar('prev')">
          {{ previousLabel }}
        </Button>
        <Button @click="shiftCalendar('next')">
          {{ nextLabel }}
        </Button>
        <RouterLink v-if="hasAction" :to="actionTo!">
          <Button type="primary">
            {{ actionLabel }}
          </Button>
        </RouterLink>
      </Space>
    </div>

    <div class="sp-dashboard__calendar-topline">
      <div>
        <strong>{{ monthLabel }}</strong>
        <p>{{ monthHint }}</p>
        <span
          v-if="loading && loadingLabel"
          aria-live="polite"
          class="sp-dashboard__calendar-loading-indicator"
          data-testid="customer-dashboard-calendar-loading-indicator"
          role="status"
        >
          <span aria-hidden="true" class="sp-dashboard__calendar-loading-dot" />
          {{ loadingLabel }}
        </span>
      </div>
      <div class="sp-dashboard__summary-chips">
        <div
          v-for="summaryItem in summary"
          :key="summaryItem.label"
          class="sp-dashboard__summary-chip"
        >
          <span>{{ summaryItem.label }}</span>
          <strong>{{ summaryItem.value }}</strong>
        </div>
      </div>
    </div>

    <div class="sp-dashboard__calendar-grid">
      <div
        v-for="label in weekDayLabels"
        :key="label"
        class="sp-dashboard__weekday"
      >
        {{ label }}
      </div>
      <div
        v-for="cell in cells"
        :key="cell.dateKey"
        class="sp-dashboard__calendar-cell"
        :class="{
          'is-muted': !cell.inMonth,
          'is-today': cell.isToday,
        }"
      >
        <span class="sp-dashboard__calendar-day">{{ cell.dayLabel }}</span>
        <div
          v-if="cell.visibleItems.length"
          class="sp-dashboard__calendar-items"
        >
          <component
            :is="item.route ? 'RouterLink' : 'div'"
            v-for="item in cell.visibleItems"
            :key="item.key"
            :to="item.route"
            class="sp-dashboard__calendar-item"
            :class="`sp-dashboard__calendar-item--${item.tone}`"
            :aria-label="`${item.coverageStateLabel}: ${item.label}`"
            :title="`${item.coverageStateLabel}: ${item.label}`"
          >
            <span
              aria-hidden="true"
              class="sp-dashboard__calendar-item-marker"
            />
            <span class="sp-dashboard__calendar-item-label">{{ item.label }}</span>
          </component>
          <button
            v-if="cell.moreCount"
            type="button"
            class="sp-dashboard__calendar-more"
            @click="toggleDay(cell.dateKey)"
          >
            +{{ cell.moreCount }} {{ moreLabel }}
          </button>
        </div>
        <div class="sp-dashboard__calendar-events">
          <span
            v-if="cell.orderCount"
            class="sp-dashboard__calendar-pill sp-dashboard__calendar-pill--amber"
          >
            {{ cell.orderCount }} {{ orderShortLabel }}
          </span>
          <span
            v-if="cell.shiftCount"
            class="sp-dashboard__calendar-pill sp-dashboard__calendar-pill--teal"
          >
            {{ cell.shiftCount }} {{ shiftShortLabel }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>

<style scoped>
.sp-dashboard__calendar-card {
  padding: 1.25rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.25rem;
  box-shadow: var(--sp-shadow-card);
  background: linear-gradient(180deg, rgb(255 255 255 / 0.96), rgb(255 255 255 / 0.84));
}

[data-theme='dark'] .sp-dashboard__calendar-card {
  background: linear-gradient(180deg, rgb(13 24 26 / 0.98), rgb(13 24 26 / 0.9));
}

.sp-dashboard__panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-dashboard__calendar-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1rem;
}

.sp-dashboard__calendar-topline strong {
  color: var(--sp-color-text-primary);
  font-size: 1.2rem;
}

.sp-dashboard__calendar-topline p {
  margin: 0.32rem 0 0;
  color: var(--sp-color-text-secondary);
}

.sp-dashboard__calendar-loading-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  width: fit-content;
  padding: 0.3rem 0.55rem;
  margin-top: 0.45rem;
  border: 1px solid color-mix(in srgb, var(--sp-color-primary-strong) 22%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  color: var(--sp-color-primary-strong);
  font-size: 0.75rem;
  font-weight: 700;
}

.sp-dashboard__calendar-loading-dot {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 999px;
  background: currentColor;
  animation: sp-dashboard-calendar-loading-pulse 1s ease-in-out infinite;
}

@keyframes sp-dashboard-calendar-loading-pulse {
  0%,
  100% {
    opacity: 0.38;
    transform: scale(0.85);
  }

  50% {
    opacity: 1;
    transform: scale(1);
  }
}

.sp-dashboard__summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.sp-dashboard__summary-chip {
  min-width: 7rem;
  padding: 0.8rem 0.95rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-dashboard__summary-chip span {
  display: block;
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
}

.sp-dashboard__summary-chip strong {
  display: block;
  margin-top: 0.25rem;
}

.sp-dashboard__calendar-grid {
  display: grid;
  gap: 0.65rem;
  margin-top: 1rem;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.sp-dashboard__weekday {
  padding: 0 0.25rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sp-dashboard__calendar-cell {
  display: grid;
  gap: 0.65rem;
  align-content: flex-start;
  min-height: 7.25rem;
  padding: 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-dashboard__calendar-cell.is-muted {
  opacity: 0.58;
}

.sp-dashboard__calendar-cell.is-today {
  border-color: rgb(40 170 170 / 48%);
  box-shadow: inset 0 0 0 1px rgb(40 170 170 / 22%);
}

.sp-dashboard__calendar-day {
  color: var(--sp-color-text-primary);
  font-weight: 700;
}

.sp-dashboard__calendar-items {
  display: grid;
  gap: 0.4rem;
}

.sp-dashboard__calendar-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.25rem;
  border-radius: 0.4rem;
  color: inherit;
  text-decoration: none;
  background: rgb(246 248 250 / 0.96);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
  border: 1px solid transparent;
}

.sp-dashboard__calendar-item:hover,
.sp-dashboard__calendar-item:focus-visible {
  transform: translateY(-1px);
  border-color: rgb(40 170 170 / 38%);
  box-shadow: var(--sp-shadow-card);
  outline: none;
}

.sp-dashboard__calendar-item--good {
  background: rgb(232 248 247 / 0.96);
}

.sp-dashboard__calendar-item--warn {
  background: rgb(255 246 223 / 0.98);
}

.sp-dashboard__calendar-item--bad {
  background: rgb(252 234 232 / 0.98);
}

.sp-dashboard__calendar-item-marker {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.78;
}

.sp-dashboard__calendar-item--good .sp-dashboard__calendar-item-marker {
  color: rgb(17 119 119);
}

.sp-dashboard__calendar-item--warn .sp-dashboard__calendar-item-marker {
  color: rgb(149 97 18);
}

.sp-dashboard__calendar-item--bad .sp-dashboard__calendar-item-marker {
  color: rgb(172 54 41);
}

.sp-dashboard__calendar-item-label {
  color: var(--sp-color-text-primary);
  font-size: 0.65rem;
  font-weight: 600;
  line-height: 1;
  min-width: 0;
}

.sp-dashboard__calendar-more {
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--sp-color-primary-strong);
  font-size: 0.76rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-dashboard__calendar-more:hover,
.sp-dashboard__calendar-more:focus-visible {
  text-decoration: underline;
  outline: none;
}

.sp-dashboard__calendar-events {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}

.sp-dashboard__calendar-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 0.14rem 0.45rem 0.14rem 0.25rem;
  border-radius: 999px;
  font-size: 0.65rem;
  font-weight: 700;
}

.sp-dashboard__calendar-pill--teal {
  background: rgb(214 245 243);
  color: rgb(17 119 119);
}

.sp-dashboard__calendar-pill--amber {
  background: rgb(255 239 196);
  color: rgb(149 97 18);
}

[data-theme='dark'] .sp-dashboard__calendar-pill--teal {
  background: rgb(13 51 53);
  color: rgb(126 225 225);
}

[data-theme='dark'] .sp-dashboard__calendar-pill--amber {
  background: rgb(69 50 13);
  color: rgb(255 214 117);
}

[data-theme='dark'] .sp-dashboard__calendar-item {
  background: rgb(24 33 35 / 0.96);
}

[data-theme='dark'] .sp-dashboard__calendar-item--good {
  background: rgb(14 42 43 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--warn {
  background: rgb(56 43 18 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--bad {
  background: rgb(70 29 26 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--good .sp-dashboard__calendar-item-marker {
  color: rgb(126 225 225);
}

[data-theme='dark'] .sp-dashboard__calendar-item--warn .sp-dashboard__calendar-item-marker {
  color: rgb(255 214 117);
}

[data-theme='dark'] .sp-dashboard__calendar-item--bad .sp-dashboard__calendar-item-marker {
  color: rgb(255 151 136);
}

@media (max-width: 960px) {
  .sp-dashboard__calendar-topline {
    display: grid;
    grid-template-columns: 1fr;
  }

  .sp-dashboard__calendar-grid {
    grid-template-columns: 1fr;
  }

  .sp-dashboard__weekday {
    display: none;
  }

  .sp-dashboard__calendar-cell {
    min-height: auto;
  }

  .sp-dashboard__panel-head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
