const REMEMBERED_IDENTIFIER_KEY = 'sicherplan.auth.remembered.identifier';
const REMEMBERED_TENANT_CODE_KEY = 'sicherplan.auth.remembered.tenant';

export interface RememberedLoginValues {
  identifier: string;
  rememberMe: boolean;
  tenantCode: string;
}

function canUseLocalStorage() {
  return typeof window !== 'undefined';
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
