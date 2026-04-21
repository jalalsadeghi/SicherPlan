<script lang="ts" setup>
import { computed, ref, watch } from "vue";

import DashboardCalendarPanel from "#/components/sicherplan/dashboard-calendar-panel.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { listStaffingBoard, type StaffingBoardShiftItem } from "@/api/planningStaffing";
import type { EmployeeOperationalRead } from "@/api/employeeAdmin";
import {
  buildEmployeeShiftsByDay,
  filterShiftsForEmployee,
  groupEmployeeProjectsFromShifts,
  mapEmployeeShiftsToCalendarCells,
  type EmployeeProjectTone,
} from "@/features/employees/employeeDashboard.helpers";
import { useI18n } from "@/i18n";

interface ProjectCard {
  key: string;
  label: string;
  meta: string;
  orderNo: string;
  shiftCount: number;
  tone: EmployeeProjectTone;
  windowLabel: string;
}

const props = defineProps<{
  accessToken: string;
  canManagePhoto: boolean;
  canReadStaffing: boolean;
  employee: EmployeeOperationalRead;
  photoUploading?: boolean;
  photoPreviewUrl?: string;
  selectedEmployeeBranchLabel?: string;
  selectedEmployeeMandateLabel?: string;
  tenantId: string;
}>();

const emit = defineEmits<{
  photoSelected: [file: File];
}>();

const { t, locale } = useI18n();
const activeDate = ref(new Date());
const expandedDays = ref<string[]>([]);
const photoInput = ref<HTMLInputElement | null>(null);
const calendarLoading = ref(false);
const projectLoading = ref(false);
const dashboardError = ref("");
const monthShiftsByDay = ref<Map<string, StaffingBoardShiftItem[]>>(new Map());
const projectShifts = ref<StaffingBoardShiftItem[]>([]);
const requestVersion = ref(0);
const monthCache = new Map<string, Map<string, StaffingBoardShiftItem[]>>();
const monthRequests = new Map<string, Promise<Map<string, StaffingBoardShiftItem[]>>>();

const employeeInitials = computed(() =>
  [props.employee.first_name, props.employee.last_name]
    .map((part) => `${part ?? ""}`.trim().charAt(0))
    .filter(Boolean)
    .join("")
    .slice(0, 2)
    .toUpperCase() || "?",
);

const employeeFullName = computed(() => `${props.employee.first_name} ${props.employee.last_name}`.trim());

const contactLabel = computed(() =>
  props.employee.work_email
  || props.employee.mobile_phone
  || props.employee.work_phone
  || t("employeeAdmin.summary.none"),
);

const photoActionLabel = computed(() =>
  props.photoPreviewUrl ? t("employeeAdmin.dashboard.photo.change") : t("employeeAdmin.dashboard.photo.add"),
);

const weekDayLabels = computed(() => {
  const monday = new Date(Date.UTC(2026, 2, 23));
  return Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(locale.value, { weekday: "short" }).format(
      new Date(monday.getUTCFullYear(), monday.getUTCMonth(), monday.getUTCDate() + index),
    ),
  );
});

const monthLabel = computed(() =>
  new Intl.DateTimeFormat(locale.value, { month: "long", year: "numeric" }).format(activeDate.value),
);

const calendarRows = computed(() => [...monthShiftsByDay.value.values()].flat());

const calendarSummary = computed(() => {
  const rows = calendarRows.value;
  return [
    { label: t("employeeAdmin.dashboard.calendarSummary.shifts"), value: String(rows.length) },
    {
      label: t("employeeAdmin.dashboard.calendarSummary.orders"),
      value: String(new Set(rows.map((row) => row.order_id).filter(Boolean)).size),
    },
    {
      label: t("employeeAdmin.dashboard.calendarSummary.projects"),
      value: String(new Set(rows.map((row) => row.planning_record_id).filter(Boolean)).size),
    },
  ];
});

const calendarCells = computed(() =>
  mapEmployeeShiftsToCalendarCells(calendarRows.value, activeDate.value, {
    expandedDays: expandedDays.value,
    locale: locale.value,
  }),
);

const projectCards = computed<ProjectCard[]>(() => {
  return groupEmployeeProjectsFromShifts(projectShifts.value, new Date()).map((project) => ({
    key: project.key,
    label: project.label,
    meta: project.meta || t("employeeAdmin.summary.none"),
    orderNo: project.orderNo,
    shiftCount: project.shiftCount,
    tone: project.tone,
    windowLabel: `${formatDate(project.startsAt)} - ${formatDate(project.endsAt)}`,
  }));
});

function formatDateTimeLocalValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function visibleCalendarMonthStart(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1, 0, 0, 0, 0);
}

function visibleCalendarMonthEnd(value: Date) {
  return new Date(value.getFullYear(), value.getMonth() + 1, 0, 23, 59, 0, 0);
}

function projectWindowStart() {
  const value = new Date();
  value.setMonth(value.getMonth() - 6);
  value.setHours(0, 0, 0, 0);
  return value;
}

function projectWindowEnd() {
  const value = new Date();
  value.setMonth(value.getMonth() + 6);
  value.setHours(23, 59, 0, 0);
  return value;
}

function formatDate(value: Date) {
  return new Intl.DateTimeFormat(locale.value, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(value);
}

function filterEmployeeShifts(shifts: StaffingBoardShiftItem[]) {
  return filterShiftsForEmployee(shifts, props.employee.id);
}

function resolveMonthKey() {
  if (!props.tenantId || !props.accessToken || !props.employee.id || !props.canReadStaffing) {
    return "";
  }
  return [
    props.tenantId,
    props.employee.id,
    formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
    formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
  ].join(":");
}

async function loadProjectWindow() {
  if (!props.tenantId || !props.accessToken || !props.employee.id || !props.canReadStaffing) {
    projectShifts.value = [];
    return;
  }
  projectLoading.value = true;
  dashboardError.value = "";
  try {
    const rows = await listStaffingBoard(props.tenantId, props.accessToken, {
      date_from: formatDateTimeLocalValue(projectWindowStart()),
      date_to: formatDateTimeLocalValue(projectWindowEnd()),
    });
    projectShifts.value = filterEmployeeShifts(rows);
  } catch {
    projectShifts.value = [];
    dashboardError.value = t("employeeAdmin.dashboard.loadError");
  } finally {
    projectLoading.value = false;
  }
}

async function loadCalendarMonth(options: { force?: boolean } = {}) {
  const monthKey = resolveMonthKey();
  if (!monthKey) {
    monthShiftsByDay.value = new Map();
    return;
  }
  const cached = monthCache.get(monthKey);
  if (cached && !options.force) {
    monthShiftsByDay.value = cached;
    return;
  }
  monthShiftsByDay.value = cached ?? new Map();
  calendarLoading.value = true;
  dashboardError.value = "";

  let request = monthRequests.get(monthKey);
  if (!request || options.force) {
    request = listStaffingBoard(props.tenantId, props.accessToken, {
      date_from: formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
      date_to: formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
    }).then((rows) => buildEmployeeShiftsByDay(filterEmployeeShifts(rows)));
    monthRequests.set(monthKey, request);
    void request.finally(() => {
      if (monthRequests.get(monthKey) === request) {
        monthRequests.delete(monthKey);
      }
    });
  }

  const version = ++requestVersion.value;
  try {
    const itemsByDay = await request;
    monthCache.set(monthKey, itemsByDay);
    if (version !== requestVersion.value || resolveMonthKey() !== monthKey) {
      return;
    }
    monthShiftsByDay.value = itemsByDay;
  } catch {
    if (version !== requestVersion.value || resolveMonthKey() !== monthKey) {
      return;
    }
    monthShiftsByDay.value = new Map();
    dashboardError.value = t("employeeAdmin.dashboard.loadError");
  } finally {
    if (version === requestVersion.value) {
      calendarLoading.value = false;
    }
  }
}

function shiftCalendar(direction: "next" | "prev") {
  const nextDate = new Date(activeDate.value);
  nextDate.setMonth(nextDate.getMonth() + (direction === "next" ? 1 : -1));
  activeDate.value = nextDate;
  expandedDays.value = [];
}

function toggleCalendarDay(dateKey: string) {
  if (expandedDays.value.includes(dateKey)) {
    expandedDays.value = expandedDays.value.filter((value) => value !== dateKey);
    return;
  }
  expandedDays.value = [...expandedDays.value, dateKey];
}

function openPhotoPicker() {
  if (!props.canManagePhoto || props.photoUploading) {
    return;
  }
  photoInput.value?.click();
}

function onDashboardPhotoSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  target.value = "";
  if (file) {
    emit("photoSelected", file);
  }
}

watch(
  () => [props.employee.id, props.tenantId, props.accessToken, props.canReadStaffing],
  () => {
    monthCache.clear();
    monthRequests.clear();
    expandedDays.value = [];
    void loadProjectWindow();
    void loadCalendarMonth({ force: true });
  },
  { immediate: true },
);

watch(
  () => [activeDate.value.getFullYear(), activeDate.value.getMonth()],
  () => {
    void loadCalendarMonth();
  },
);
</script>

<template>
  <section class="employee-dashboard-tab" data-testid="employee-dashboard-panel">
    <section class="employee-dashboard-tab__hero" data-testid="employee-dashboard-hero">
      <div class="employee-dashboard-tab__photo" data-testid="employee-dashboard-photo">
        <button
          type="button"
          class="employee-dashboard-tab__photo-button"
          :aria-label="photoActionLabel"
          :disabled="!canManagePhoto || photoUploading"
          :title="photoActionLabel"
          data-testid="employee-dashboard-photo-button"
          @click="openPhotoPicker"
        >
          <img
            v-if="photoPreviewUrl"
            :src="photoPreviewUrl"
            :alt="t('employeeAdmin.dashboard.photo.alt')"
            data-testid="employee-dashboard-photo-image"
          />
          <span v-else data-testid="employee-dashboard-photo-placeholder">{{ employeeInitials }}</span>
          <span class="employee-dashboard-tab__photo-hint">{{ photoActionLabel }}</span>
          <span
            v-if="photoUploading"
            class="employee-dashboard-tab__photo-uploading"
            data-testid="employee-dashboard-photo-uploading"
          >
            {{ t("employeeAdmin.dashboard.photo.uploading") }}
          </span>
        </button>
        <input
          ref="photoInput"
          class="employee-dashboard-tab__photo-input"
          data-testid="employee-dashboard-photo-input"
          type="file"
          accept="image/*"
          :disabled="!canManagePhoto || photoUploading"
          @change="onDashboardPhotoSelected"
        />
      </div>
      <div class="employee-dashboard-tab__summary" data-testid="employee-dashboard-summary">
        <div>
          <h3>{{ employeeFullName }}</h3>
          <p v-if="employee.preferred_name && employee.preferred_name !== employeeFullName">
            {{ employee.preferred_name }}
          </p>
        </div>
        <div class="employee-dashboard-tab__chips">
          <span>{{ employee.personnel_no }}</span>
          <span>{{ contactLabel }}</span>
          <span>{{ selectedEmployeeBranchLabel || t("employeeAdmin.summary.none") }}</span>
          <span>{{ selectedEmployeeMandateLabel || t("employeeAdmin.summary.none") }}</span>
          <StatusBadge :status="employee.status" />
        </div>
      </div>
    </section>

    <section class="employee-dashboard-tab__projects" data-testid="employee-dashboard-projects">
      <div class="employee-dashboard-tab__section-head">
        <div>
          <p class="eyebrow">{{ t("employeeAdmin.dashboard.projectsEyebrow") }}</p>
          <h3>{{ t("employeeAdmin.dashboard.projectsTitle") }}</h3>
        </div>
        <span v-if="projectLoading" class="employee-dashboard-tab__loading">{{ t("workspace.loading.processing") }}</span>
      </div>
      <p v-if="!canReadStaffing" class="employee-dashboard-tab__state">
        {{ t("employeeAdmin.dashboard.noStaffingAccess") }}
      </p>
      <p v-else-if="dashboardError" class="employee-dashboard-tab__state">
        {{ dashboardError }}
      </p>
      <p v-else-if="!projectLoading && !projectCards.length" class="employee-dashboard-tab__state">
        {{ t("employeeAdmin.dashboard.projectsEmpty") }}
      </p>
      <div v-else class="employee-dashboard-tab__project-grid">
        <article
          v-for="project in projectCards"
          :key="project.key"
          class="employee-dashboard-tab__project-card"
          :class="`employee-dashboard-tab__project-card--${project.tone}`"
          data-testid="employee-dashboard-project-card"
        >
          <span>{{ t(`employeeAdmin.dashboard.projectStatus.${project.tone}` as never) }}</span>
          <strong>{{ project.label }}</strong>
          <small>{{ project.orderNo }} · {{ project.windowLabel }}</small>
          <small>{{ project.shiftCount }} {{ t("employeeAdmin.dashboard.projectShiftCount") }} · {{ project.meta }}</small>
        </article>
      </div>
    </section>

    <DashboardCalendarPanel
      v-if="canReadStaffing"
      :cells="calendarCells"
      :description="t('employeeAdmin.dashboard.calendarDescription')"
      :loading="calendarLoading"
      :loading-label="t('workspace.loading.processing')"
      :month-hint="t('employeeAdmin.dashboard.calendarMonthHint')"
      :month-label="monthLabel"
      :more-label="t('employeeAdmin.dashboard.calendarMore')"
      :next-label="t('employeeAdmin.dashboard.calendarNext')"
      :order-short-label="t('employeeAdmin.dashboard.calendarOrderShort')"
      :previous-label="t('employeeAdmin.dashboard.calendarPrevious')"
      :shift-short-label="t('employeeAdmin.dashboard.calendarShiftShort')"
      :summary="calendarSummary"
      :title="t('employeeAdmin.dashboard.calendarTitle')"
      :week-day-labels="weekDayLabels"
      data-testid="employee-dashboard-calendar"
      @shift-calendar="shiftCalendar"
      @toggle-day="toggleCalendarDay"
    />
  </section>
</template>

<style scoped>
.employee-dashboard-tab {
  display: grid;
  gap: 1rem;
}

.employee-dashboard-tab__hero,
.employee-dashboard-tab__projects {
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.employee-dashboard-tab__hero {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
}

.employee-dashboard-tab__photo {
  display: grid;
  place-items: center;
  width: 10rem;
  height: 10rem;
}

.employee-dashboard-tab__photo-button {
  position: relative;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  padding: 0;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--sp-color-primary) 30%, transparent);
  border-radius: 6px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 72%, transparent);
  color: var(--sp-color-primary-strong);
  cursor: pointer;
  font-size: 1.4rem;
  font-weight: 800;
}

.employee-dashboard-tab__photo-button:disabled {
  cursor: default;
}

.employee-dashboard-tab__photo-button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--sp-color-primary) 55%, transparent);
  outline-offset: 3px;
}

.employee-dashboard-tab__photo-button img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.employee-dashboard-tab__photo-input {
  display: none;
}

.employee-dashboard-tab__photo-hint,
.employee-dashboard-tab__photo-uploading {
  position: absolute;
  right: 0.45rem;
  bottom: 0.45rem;
  left: 0.45rem;
  padding: 0.28rem 0.45rem;
  border-radius: 999px;
  background: rgb(15 23 42 / 0.78);
  color: white;
  font-size: 0.72rem;
  font-weight: 800;
  text-align: center;
}

.employee-dashboard-tab__photo-uploading {
  background: color-mix(in srgb, var(--sp-color-primary-strong) 82%, black);
}

.employee-dashboard-tab__photo-button:disabled .employee-dashboard-tab__photo-hint {
  display: none;
}

.employee-dashboard-tab__summary {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
}

.employee-dashboard-tab__summary h3
{
  font-weight: 600;
}

.employee-dashboard-tab__summary h3,
.employee-dashboard-tab__summary p {
  margin: 0;
}

.employee-dashboard-tab__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.employee-dashboard-tab__chips span {
  padding: 0.34rem 0.55rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 999px;
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
}

.employee-dashboard-tab__section-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.employee-dashboard-tab__section-head h3 {
  margin: 0;
}

.employee-dashboard-tab__loading,
.employee-dashboard-tab__state {
  color: var(--sp-color-text-secondary);
}

.employee-dashboard-tab__project-grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 1rem;
}

.employee-dashboard-tab__project-card {
  display: grid;
  gap: 0.35rem;
  padding: 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 16px;
  background: var(--sp-color-surface-page);
}

.employee-dashboard-tab__project-card span {
  width: fit-content;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 800;
}

.employee-dashboard-tab__project-card--past span {
  background: rgb(100 116 139 / 0.16);
  color: rgb(71 85 105);
}

.employee-dashboard-tab__project-card--current span {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 75%, transparent);
  color: var(--sp-color-primary-strong);
}

.employee-dashboard-tab__project-card--future span {
  background: rgb(59 130 246 / 0.14);
  color: rgb(29 78 216);
}

.employee-dashboard-tab__project-card strong {
  color: var(--sp-color-text-primary);
}

.employee-dashboard-tab__project-card small {
  color: var(--sp-color-text-secondary);
}

@media (max-width: 960px) {
  .employee-dashboard-tab__project-grid {
    grid-template-columns: 1fr;
  }

  .employee-dashboard-tab__hero {
    grid-template-columns: 1fr;
  }
}
</style>
