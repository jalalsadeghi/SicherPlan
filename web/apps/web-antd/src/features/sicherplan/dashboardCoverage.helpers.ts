import type { CoverageShiftItem } from "@/api/planningStaffing";

function formatDateTimeLocalValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatTimeLabel(value: string, locale: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatShiftTypeLabel(value: string) {
  return value
    .split(/[_-]+/u)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function truncateCalendarLabel(value: string, maxLength = 24) {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 1).trimEnd()}…`;
}

export function buildCanonicalStaffingWindow(coverageRow: CoverageShiftItem) {
  const start = new Date(coverageRow.starts_at);
  const end = new Date(coverageRow.ends_at);
  const dateFrom = new Date(start.getFullYear(), start.getMonth(), start.getDate(), 0, 0, 0, 0);
  const dateTo = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1, 0, 0, 0, 0);
  return {
    date_from: formatDateTimeLocalValue(dateFrom),
    date_to: formatDateTimeLocalValue(dateTo),
  };
}

export function buildCoverageShiftLabel(coverageRow: CoverageShiftItem, locale: string) {
  const shiftTypeLabel = formatShiftTypeLabel(coverageRow.shift_type_code);
  const timeWindow = `${formatTimeLabel(coverageRow.starts_at, locale)}-${formatTimeLabel(coverageRow.ends_at, locale)}`;
  const contextLabel = coverageRow.planning_record_name || coverageRow.location_text || coverageRow.order_no;
  return truncateCalendarLabel([shiftTypeLabel, timeWindow, contextLabel].filter(Boolean).join(" · "), 36);
}

export function buildStaffingCoverageRoute(coverageRow: CoverageShiftItem) {
  const staffingWindow = buildCanonicalStaffingWindow(coverageRow);
  const query = new URLSearchParams({
    date_from: staffingWindow.date_from,
    date_to: staffingWindow.date_to,
    planning_record_id: coverageRow.planning_record_id,
    shift_id: coverageRow.shift_id,
  });
  return `/admin/planning-staffing?${query.toString()}`;
}
