import { describe, expect, it } from 'vitest';

import {
  buildEmployeeOperationalPayload,
  filterMandatesForBranch,
  formatEmployeeStructureLabel,
} from './employeeAdmin.helpers.js';

describe('employee create payload helpers', () => {
  it('submits branch and mandate UUIDs, not display labels', () => {
    const payload = buildEmployeeOperationalPayload({
      tenant_id: 'tenant-1',
      personnel_no: ' EMP-1001 ',
      first_name: ' Anna ',
      last_name: ' Schmidt ',
      preferred_name: '',
      work_email: '',
      work_phone: '',
      mobile_phone: '',
      default_branch_id: '22222222-2222-2222-2222-222222222222',
      default_mandate_id: '33333333-3333-3333-3333-333333333333',
      hire_date: '',
      termination_date: '',
      user_id: '11111111-1111-1111-1111-111111111111',
      notes: '',
    });

    expect(payload.default_branch_id).toBe('22222222-2222-2222-2222-222222222222');
    expect(payload.default_mandate_id).toBe('33333333-3333-3333-3333-333333333333');
    expect(payload.personnel_no).toBe('EMP-1001');
  });

  it('does not keep stale free-text labels as IDs', () => {
    const branchLabel = formatEmployeeStructureLabel({ code: 'CGN', name: 'Cologne HQ' });
    const mandateLabel = formatEmployeeStructureLabel({ code: 'M-42', name: 'Night Shift' });

    const payload = buildEmployeeOperationalPayload({
      tenant_id: 'tenant-1',
      personnel_no: 'EMP-1002',
      first_name: 'Mila',
      last_name: 'Graf',
      preferred_name: '',
      work_email: '',
      work_phone: '',
      mobile_phone: '',
      default_branch_id: branchLabel,
      default_mandate_id: mandateLabel,
      hire_date: '',
      termination_date: '',
      user_id: '',
      notes: '',
    }, {
      allowedBranchIds: ['22222222-2222-2222-2222-222222222222'],
      allowedMandateIds: ['33333333-3333-3333-3333-333333333333'],
    });

    expect(branchLabel).toBe('CGN - Cologne HQ');
    expect(mandateLabel).toBe('M-42 - Night Shift');
    expect(payload.default_branch_id).toBeNull();
    expect(payload.default_mandate_id).toBeNull();
  });

  it('defers user linkage during the initial create flow', () => {
    const payload = buildEmployeeOperationalPayload(
      {
        tenant_id: 'tenant-1',
        personnel_no: 'EMP-1003',
        first_name: 'Lars',
        last_name: 'Winter',
        preferred_name: '',
        work_email: '',
        work_phone: '',
        mobile_phone: '',
        default_branch_id: '',
        default_mandate_id: '',
        hire_date: '',
        termination_date: '',
        user_id: 'usr-emp-0042',
        notes: '',
      },
      { deferUserLink: true },
    );

    expect(payload.user_id).toBeNull();
  });

  it('filters mandate options by the selected branch', () => {
    const mandates = [
      { id: 'm-1', branch_id: 'b-1', code: 'M-1', name: 'North' },
      { id: 'm-2', branch_id: 'b-2', code: 'M-2', name: 'South' },
      { id: 'm-3', branch_id: 'b-1', code: 'M-3', name: 'West' },
    ];

    expect(filterMandatesForBranch(mandates, 'b-1').map((row) => row.id)).toEqual(['m-1', 'm-3']);
    expect(filterMandatesForBranch(mandates, '').map((row) => row.id)).toEqual(['m-1', 'm-2', 'm-3']);
  });
});
