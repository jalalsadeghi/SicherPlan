const REMEMBERED_IDENTIFIER_KEY = 'sicherplan.auth.remembered.identifier';
const REMEMBERED_TENANT_CODE_KEY = 'sicherplan.auth.remembered.tenant';
const SESSION_METADATA_KEY = 'sicherplan.auth.session.metadata';

export interface RememberedLoginValues {
  identifier: string;
  rememberMe: boolean;
  tenantCode: string;
}

export interface StoredAuthSessionMetadata {
  accessTokenExpiresAt: string;
  refreshTokenExpiresAt: string;
  rememberMe: boolean;
  sessionId: string;
}

function canUseLocalStorage() {
  return typeof window !== 'undefined';
}

function emptySessionMetadata(): StoredAuthSessionMetadata {
  return {
    accessTokenExpiresAt: '',
    refreshTokenExpiresAt: '',
    rememberMe: false,
    sessionId: '',
  };
}

export function readRememberedLoginValues(): RememberedLoginValues {
  if (!canUseLocalStorage()) {
    return {
      identifier: '',
      rememberMe: false,
      tenantCode: '',
    };
  }

  const tenantCode = window.localStorage.getItem(REMEMBERED_TENANT_CODE_KEY) ?? '';
  const identifier = window.localStorage.getItem(REMEMBERED_IDENTIFIER_KEY) ?? '';

  return {
    identifier,
    rememberMe: Boolean(tenantCode || identifier),
    tenantCode,
  };
}

export function persistRememberedLoginValues(values: {
  identifier?: string;
  rememberMe?: boolean;
  tenantCode?: string;
}) {
  if (!canUseLocalStorage()) {
    return;
  }

  if (!values.rememberMe) {
    window.localStorage.removeItem(REMEMBERED_IDENTIFIER_KEY);
    window.localStorage.removeItem(REMEMBERED_TENANT_CODE_KEY);
    return;
  }

  const tenantCode = values.tenantCode?.trim() ?? '';
  const identifier = values.identifier?.trim() ?? '';

  if (tenantCode) {
    window.localStorage.setItem(REMEMBERED_TENANT_CODE_KEY, tenantCode);
  } else {
    window.localStorage.removeItem(REMEMBERED_TENANT_CODE_KEY);
  }

  if (identifier) {
    window.localStorage.setItem(REMEMBERED_IDENTIFIER_KEY, identifier);
  } else {
    window.localStorage.removeItem(REMEMBERED_IDENTIFIER_KEY);
  }
}

export function readStoredAuthSessionMetadata(): StoredAuthSessionMetadata {
  if (!canUseLocalStorage()) {
    return emptySessionMetadata();
  }

  const rawValue = window.localStorage.getItem(SESSION_METADATA_KEY);
  if (!rawValue) {
    return emptySessionMetadata();
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<StoredAuthSessionMetadata>;
    return {
      accessTokenExpiresAt:
        typeof parsed.accessTokenExpiresAt === 'string'
          ? parsed.accessTokenExpiresAt
          : '',
      refreshTokenExpiresAt:
        typeof parsed.refreshTokenExpiresAt === 'string'
          ? parsed.refreshTokenExpiresAt
          : '',
      rememberMe: parsed.rememberMe === true,
      sessionId: typeof parsed.sessionId === 'string' ? parsed.sessionId : '',
    };
  } catch {
    return emptySessionMetadata();
  }
}

export function persistAuthSessionMetadata(
  metadata: Partial<StoredAuthSessionMetadata>,
) {
  if (!canUseLocalStorage()) {
    return;
  }

  const normalized: StoredAuthSessionMetadata = {
    accessTokenExpiresAt: metadata.accessTokenExpiresAt?.trim() ?? '',
    refreshTokenExpiresAt: metadata.refreshTokenExpiresAt?.trim() ?? '',
    rememberMe: metadata.rememberMe === true,
    sessionId: metadata.sessionId?.trim() ?? '',
  };

  if (
    !normalized.accessTokenExpiresAt
    && !normalized.refreshTokenExpiresAt
    && !normalized.sessionId
    && !normalized.rememberMe
  ) {
    window.localStorage.removeItem(SESSION_METADATA_KEY);
    return;
  }

  window.localStorage.setItem(SESSION_METADATA_KEY, JSON.stringify(normalized));
}

export function clearStoredAuthSessionMetadata() {
  if (!canUseLocalStorage()) {
    return;
  }
  window.localStorage.removeItem(SESSION_METADATA_KEY);
}
