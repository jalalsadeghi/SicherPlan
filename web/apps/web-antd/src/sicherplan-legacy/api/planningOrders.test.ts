// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';

import { listDocuments } from './planningOrders';

describe('planning orders document API', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('searches tenant documents through the platform document list endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await listDocuments('tenant-1', 'access-1', {
      document_type_code: 'customer_contract',
      linked_entity: '',
      limit: 20,
      search: 'contract',
    });

    const [requestedUrl, requestInit] = fetchMock.mock.calls[0] ?? [];
    expect(String(requestedUrl)).toContain('/api/platform/tenants/tenant-1/documents?');
    expect(String(requestedUrl)).toContain('search=contract');
    expect(String(requestedUrl)).toContain('document_type_code=customer_contract');
    expect(String(requestedUrl)).toContain('limit=20');
    expect(String(requestedUrl)).not.toContain('linked_entity=');
    expect(requestInit).toEqual(
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer access-1',
        }),
      }),
    );
  });
});
