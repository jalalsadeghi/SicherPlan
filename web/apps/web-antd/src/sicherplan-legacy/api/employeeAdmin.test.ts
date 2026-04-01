// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  accessStoreState,
  refreshTokenApi,
  syncFromPrimarySession,
} = vi.hoisted(() => {
  const state = {
    accessToken: null as null | string,
    refreshToken: null as null | string,
    setAccessToken: vi.fn((token: null | string) => {
      state.accessToken = token;
    }),
    setRefreshToken: vi.fn((token: null | string) => {
      state.refreshToken = token;
    }),
  };

  return {
    accessStoreState: state,
    refreshTokenApi: vi.fn(),
    syncFromPrimarySession: vi.fn(),
  };
});

vi.mock('@vben/stores', () => ({
  useAccessStore: () => accessStoreState,
}));

vi.mock('#/api/core/auth', () => ({
  refreshTokenApi,
}));

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    syncFromPrimarySession,
  }),
}));

import { createEmployee, EmployeeAdminApiError, listEmployees, uploadEmployeeDocument } from './employeeAdmin';

describe('employee admin auth recovery', () => {
  beforeEach(() => {
    accessStoreState.accessToken = null;
    accessStoreState.refreshToken = null;
    accessStoreState.setAccessToken.mockClear();
    accessStoreState.setRefreshToken.mockClear();
    syncFromPrimarySession.mockClear();
    refreshTokenApi.mockReset();
    vi.restoreAllMocks();
  });

  it('refreshes and retries when employee create hits an expired token', async () => {
    accessStoreState.refreshToken = 'refresh-1';
    refreshTokenApi.mockResolvedValue({
      accessToken: 'fresh-access',
      accessTokenExpiresAt: '2026-03-23T10:15:00Z',
      refreshToken: 'refresh-2',
      refreshTokenExpiresAt: '2026-03-30T10:15:00Z',
      sessionId: 'session-1',
    });

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: 'iam.auth.invalid_access_token',
              message_key: 'errors.iam.auth.invalid_access_token',
              request_id: 'req-1',
              details: {},
            },
          }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: 'emp-1',
            tenant_id: 'tenant-1',
            personnel_no: 'P-001',
            first_name: 'Nina',
            last_name: 'Nord',
            preferred_name: null,
            work_email: null,
            mobile_phone: null,
            default_branch_id: null,
            default_mandate_id: null,
            hire_date: null,
            termination_date: null,
            status: 'active',
            created_at: '2026-03-23T10:00:00Z',
            updated_at: '2026-03-23T10:00:00Z',
            archived_at: null,
            version_no: 1,
            work_phone: null,
            user_id: null,
            notes: null,
            group_memberships: [],
          }),
          {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    const response = await createEmployee('tenant-1', 'stale-access', {
      first_name: 'Nina',
      last_name: 'Nord',
      personnel_no: 'P-001',
      tenant_id: 'tenant-1',
    });

    expect(response.id).toBe('emp-1');
    expect(refreshTokenApi).toHaveBeenCalledTimes(1);
    expect(accessStoreState.setAccessToken).toHaveBeenCalledWith('fresh-access');
    expect(accessStoreState.setRefreshToken).toHaveBeenCalledWith('refresh-2');
    expect(syncFromPrimarySession).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/employees/tenants/tenant-1/employees'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer fresh-access',
        }),
      }),
    );
  });

  it('omits empty employee list filters from the query string', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await listEmployees('tenant-1', 'access-1', {
      search: '',
      status: '',
      default_branch_id: '',
      default_mandate_id: '',
      include_archived: false,
    });

    const [requestedUrl] = fetchMock.mock.calls[0] ?? [];
    expect(String(requestedUrl)).toMatch(/\/api\/employees\/tenants\/tenant-1\/employees$/);
  });

  it('includes only active employee list filters that are actually set', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await listEmployees('tenant-1', 'access-1', {
      search: 'nina',
      status: 'active',
      default_branch_id: 'branch-1',
      default_mandate_id: '',
      include_archived: true,
    });

    const [requestedUrl] = fetchMock.mock.calls[0] ?? [];
    expect(String(requestedUrl)).toContain('/api/employees/tenants/tenant-1/employees?');
    expect(String(requestedUrl)).toContain('search=nina');
    expect(String(requestedUrl)).toContain('status=active');
    expect(String(requestedUrl)).toContain('default_branch_id=branch-1');
    expect(String(requestedUrl)).toContain('include_archived=true');
    expect(String(requestedUrl)).not.toContain('default_mandate_id=');
  });

  it('surfaces raw route-level 404s as dedicated employee API errors with request id', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('Not Found', {
        status: 404,
        headers: { 'X-Request-ID': 'req-upload-404' },
      }),
    );

    await expect(
      uploadEmployeeDocument('tenant-1', 'employee-1', 'access-1', {
        title: 'Arbeitsvertrag',
        relation_type: 'contract',
        file_name: 'contract.pdf',
        content_type: 'application/pdf',
        content_base64: 'YQ==',
      }),
    ).rejects.toMatchObject({
      statusCode: 404,
      code: 'platform.http_not_found',
      messageKey: 'errors.platform.http_not_found',
      requestId: 'req-upload-404',
    });
  });
});
