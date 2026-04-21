import type { StaffingBoardShiftItem } from "@/api/planningStaffing";

export type EmployeeProjectTone = "current" | "future" | "past";
export type EmployeeCalendarTone = "bad" | "good" | "warn";

export interface EmployeeProjectContext {
  key: string;
  label: string;
  meta: string;
  orderNo: string;
  shiftCount: number;
  startsAt: Date;
  endsAt: Date;
  tone: EmployeeProjectTone;
}

export interface EmployeeCalendarCellItem {
  assignmentStatusCode: string;
  coverageStateLabel: string;
  date: string;
  key: string;
  label: string;
  locationText: null | string;
  orderNo: string;
  planningRecordName: string;
  shiftId: string;
  shiftTypeCode: string;
  timeRange: string;
  tone: EmployeeCalendarTone;
}

export interface EmployeeCalendarCell {
  dateKey: string;
  dayLabel: string;
  inMonth: boolean;
  isToday: boolean;
  moreCount: number;
  orderCount: number;
  shiftCount: number;
  visibleItems: EmployeeCalendarCellItem[];
}

export function filterShiftsForEmployee(shifts: StaffingBoardShiftItem[], employeeId: string) {
  if (!employeeId) {
    return [];
  }
  return shifts.filter((shift) => shift.assignments.some((assignment) => assignment.employee_id === employeeId));
}

export function classifyEmployeeProject(project: { endsAt: Date; startsAt: Date }, today: Date): EmployeeProjectTone {
  if (project.endsAt.getTime() < today.getTime()) {
    return "past";
  }
  if (project.startsAt.getTime() > today.getTime()) {
    return "future";
  }
  return "current";
}

export function groupEmployeeProjectsFromShifts(shifts: StaffingBoardShiftItem[], today: Date) {
  const grouped = new Map<string, StaffingBoardShiftItem[]>();
  shifts.forEach((shift) => {
    const key = shift.order_id || shift.planning_record_id || shift.shift_plan_id || shift.id;
    grouped.set(key, [...(grouped.get(key) ?? []), shift]);
  });

  return [...grouped.entries()]
    .map<EmployeeProjectContext>(([key, rows]) => {
      const sorted = [...rows].sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime());
      const first = sorted[0]!;
      const startsAt = new Date(sorted[0]!.starts_at);
      const endsAt = new Date(sorted.at(-1)!.ends_at);
      return {
        key,
        label: first.planning_record_name || first.order_no || key,
        meta: first.shift_type_code || first.workforce_scope_code || "",
        orderNo: first.order_no,
        shiftCount: sorted.length,
        startsAt,
        endsAt,
        tone: classifyEmployeeProject({ startsAt, endsAt }, today),
      };
    })
    .sort((left, right) => {
      const order: Record<EmployeeProjectTone, number> = { current: 0, future: 1, past: 2 };
      return order[left.tone] - order[right.tone] || left.label.localeCompare(right.label);
    });
}

export function mapEmployeeShiftsToCalendarCells(
  shifts: StaffingBoardShiftItem[],
  activeDate: Date,
  options: {
    expandedDays?: string[];
    locale: string;
    today?: Date;
  },
) {
  const year = activeDate.getFullYear();
  const month = activeDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(year, month, 1 - startOffset);
  const expandedDays = options.expandedDays ?? [];
  const todayKey = buildEmployeeDashboardDayKey(options.today ?? new Date());
  const shiftsByDay = buildEmployeeShiftsByDay(shifts);

  return Array.from({ length: 35 }, (_, index) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + index);
    const dayKey = buildEmployeeDashboardDayKey(date);
    const dayShifts = shiftsByDay.get(dayKey) ?? [];
    const isExpanded = expandedDays.includes(dayKey);
    const visibleItems = (isExpanded ? dayShifts : dayShifts.slice(0, 2)).map((shift) =>
      mapEmployeeShiftToCalendarItem(shift, date, options.locale),
    );
    return {
      dateKey: dayKey,
      dayLabel: String(date.getDate()),
      inMonth: date.getMonth() === month,
      isToday: dayKey === todayKey,
      moreCount: Math.max(dayShifts.length - visibleItems.length, 0),
      orderCount: new Set(dayShifts.map((shift) => shift.order_id).filter(Boolean)).size,
      shiftCount: dayShifts.length,
      visibleItems,
    };
  });
}

export function buildEmployeeShiftsByDay(shifts: StaffingBoardShiftItem[]) {
  const itemsByDay = new Map<string, StaffingBoardShiftItem[]>();
  [...shifts]
    .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime())
    .forEach((shift) => {
      const key = buildEmployeeDashboardDayKey(new Date(shift.starts_at));
      itemsByDay.set(key, [...(itemsByDay.get(key) ?? []), shift]);
    });
  return itemsByDay;
}

export function buildEmployeeDashboardDayKey(value: Date) {
  return value.toDateString();
}

function mapEmployeeShiftToCalendarItem(shift: StaffingBoardShiftItem, date: Date, locale: string): EmployeeCalendarCellItem {
  const assignment = shift.assignments.find((row) => row.employee_id);
  const timeRange = formatEmployeeDashboardTimeRange(shift.starts_at, shift.ends_at, locale);
  const context = shift.order_no || shift.planning_record_name || shift.shift_type_code;
  return {
    assignmentStatusCode: assignment?.assignment_status_code ?? "",
    coverageStateLabel: assignment?.assignment_status_code || shift.release_state || shift.status,
    date: buildEmployeeDashboardDayKey(date),
    key: shift.id,
    label: `${timeRange} ${context}`,
    locationText: shift.location_text,
    orderNo: shift.order_no,
    planningRecordName: shift.planning_record_name,
    shiftId: shift.id,
    shiftTypeCode: shift.shift_type_code,
    timeRange,
    tone: resolveEmployeeCalendarTone(shift),
  };
}

function formatEmployeeDashboardTimeRange(startsAt: string, endsAt: string, locale: string) {
  const formatter = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${formatter.format(new Date(startsAt))}-${formatter.format(new Date(endsAt))}`;
}

function resolveEmployeeCalendarTone(shift: StaffingBoardShiftItem): EmployeeCalendarTone {
  if (shift.release_state === "released") {
    return "good";
  }
  if (shift.release_state === "release_ready") {
    return "warn";
  }
  return "bad";
}
