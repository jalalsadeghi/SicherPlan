import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';


describe('assistant ui action metadata for employee create', () => {
  it('assistant_ui_action_metadata_exists_for_employee_create', () => {
    const viewSource = readFileSync(
      resolve(process.cwd(), 'src/sicherplan-legacy/views/EmployeeAdminView.vue'),
      'utf8',
    );

    expect(viewSource).toContain('data-assistant-action="employees.create.open"');
    expect(viewSource).toContain('data-assistant-page-id="E-01"');
    expect(viewSource).toContain('data-testid="employee-list-header-new-employee"');
    expect(viewSource).toContain('t("employeeAdmin.actions.newEmployee")');
  });
});
