import { describe, expect, it } from "vitest";

import type { StaffingBoardShiftItem } from "@/api/planningStaffing";
import {
  classifyEmployeeProject,
  filterShiftsForEmployee,
  groupEmployeeProjectsFromShifts,
  mapEmployeeShiftsToCalendarCells,
} from "./employeeDashboard.helpers";

function buildShift(
  id: string,
  employeeId: null | string,
  startsAt: string,
  endsAt: string,
  overrides: Partial<StaffingBoardShiftItem> = {},
): StaffingBoardShiftItem {
  return {
    id,
    tenant_id: "tenant-1",
    planning_record_id: `planning-${id}`,
    shift_plan_id: `plan-${id}`,
    order_id: `order-${id}`,
    order_no: `ORD-${id}`,
    planning_record_name: `Planning ${id}`,
    planning_mode_code: "site",
    workforce_scope_code: "internal",
    starts_at: startsAt,
    ends_at: endsAt,
    shift_type_code: "regular",
    release_state: "released",
    status: "active",
    location_text: "Gate 1",
    meeting_point: null,
    demand_groups: [],
    assignments: [
      {
        id: `assignment-${id}`,
        shift_id: id,
        demand_group_id: `demand-${id}`,
        team_id: null,
        employee_id: employeeId,
        subcontractor_worker_id: null,
        assignment_status_code: "assigned",
        assignment_source_code: "manual",
        confirmed_at: null,
        version_no: 1,
      },
    ],
    ...overrides,
  };
}

describe("employeeDashboard helpers", () => {
  it("filters staffing-board shifts by assignment employee_id", () => {
    const shifts = [
      buildShift("shift-1", "employee-1", "2026-04-21T08:00:00Z", "2026-04-21T16:00:00Z"),
      buildShift("shift-2", "employee-2", "2026-04-21T09:00:00Z", "2026-04-21T17:00:00Z"),
      buildShift("shift-3", null, "2026-04-21T10:00:00Z", "2026-04-21T18:00:00Z"),
    ];

    expect(filterShiftsForEmployee(shifts, "employee-1").map((shift) => shift.id)).toEqual(["shift-1"]);
    expect(filterShiftsForEmployee(shifts, "")).toEqual([]);
  });

  it("groups assigned shifts into past, current, and future project contexts", () => {
    const today = new Date("2026-04-21T12:00:00Z");
    const shifts = [
      buildShift("current-1", "employee-1", "2026-04-20T08:00:00Z", "2026-04-21T16:00:00Z", {
        order_id: "order-current",
        order_no: "ORD-CURRENT",
        planning_record_name: "Current Patrol",
      }),
      buildShift("current-2", "employee-1", "2026-04-21T18:00:00Z", "2026-04-22T02:00:00Z", {
        order_id: "order-current",
        order_no: "ORD-CURRENT",
        planning_record_name: "Current Patrol",
      }),
      buildShift("future-1", "employee-1", "2026-05-02T08:00:00Z", "2026-05-02T16:00:00Z", {
        order_id: "order-future",
        order_no: "ORD-FUTURE",
        planning_record_name: "Future Patrol",
      }),
      buildShift("past-1", "employee-1", "2026-03-01T08:00:00Z", "2026-03-01T16:00:00Z", {
        order_id: "order-past",
        order_no: "ORD-PAST",
        planning_record_name: "Past Patrol",
      }),
    ];

    const projects = groupEmployeeProjectsFromShifts(shifts, today);
    expect(projects.map((project) => [project.orderNo, project.tone, project.shiftCount])).toEqual([
      ["ORD-CURRENT", "current", 2],
      ["ORD-FUTURE", "future", 1],
      ["ORD-PAST", "past", 1],
    ]);
    expect(classifyEmployeeProject({ startsAt: new Date("2026-04-22T00:00:00Z"), endsAt: new Date("2026-04-22T08:00:00Z") }, today)).toBe("future");
  });

  it("maps only provided employee shifts into dashboard calendar cells with shift context", () => {
    const cells = mapEmployeeShiftsToCalendarCells(
      [
        buildShift("shift-1", "employee-1", "2026-04-21T08:00:00Z", "2026-04-21T16:00:00Z", {
          order_no: "ORD-100",
          planning_record_name: "City Center Patrol",
        }),
      ],
      new Date("2026-04-01T00:00:00Z"),
      {
        locale: "en-US",
        today: new Date("2026-04-21T12:00:00Z"),
      },
    );

    const activeCell = cells.find((cell) => cell.visibleItems.some((item) => item.shiftId === "shift-1"));
    expect(activeCell).toBeDefined();
    expect(activeCell?.shiftCount).toBe(1);
    expect(activeCell?.orderCount).toBe(1);
    expect(activeCell?.isToday).toBe(true);
    expect(activeCell?.visibleItems[0]).toMatchObject({
      assignmentStatusCode: "assigned",
      locationText: "Gate 1",
      orderNo: "ORD-100",
      planningRecordName: "City Center Patrol",
      shiftId: "shift-1",
      shiftTypeCode: "regular",
      tone: "good",
    });
    expect(activeCell?.visibleItems[0]?.label).toContain("ORD-100");
  });
});
