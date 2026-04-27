import { useAccessStore } from '@vben/stores';
import { preferences } from '@vben/preferences';

export type AssistantLanguageCode = string;

export type AssistantConfidence = 'low' | 'medium' | 'high';

export type AssistantFindingSeverity = 'info' | 'warning' | 'blocking';

export interface AssistantCapabilities {
  enabled: boolean;
  provider_mode?: 'openai' | 'mock' | string;
  openai_configured?: boolean;
  mock_provider_allowed?: boolean;
  rag_enabled?: boolean;
  can_chat: boolean;
  can_run_diagnostics?: boolean;
  can_reindex_knowledge?: boolean;
  supported_features?: string[];
}

export interface AssistantProviderStatus {
  provider_mode: 'openai' | 'mock' | string;
  openai_configured: boolean;
  model: string;
  mock_provider_allowed: boolean;
  store_responses: boolean;
  rag_enabled: boolean;
}

export interface AssistantRouteContext {
  path: string;
  route_name?: null | string;
  page_id?: null | string;
  query?: Record<string, unknown>;
  ui_locale?: null | string;
  timezone?: null | string;
  visible_page_title?: null | string;
}

export interface AssistantClientContext {
  timezone?: null | string;
  ui_locale?: null | string;
  visible_page_title?: null | string;
}

export interface AssistantDiagnosisItem {
  finding: string;
  severity: AssistantFindingSeverity;
  evidence?: null | string;
}

export interface AssistantLink {
  label: string;
  path: string;
  route_name?: null | string;
  page_id?: null | string;
  reason?: null | string;
}

export interface AssistantMissingPermission {
  permission: string;
  reason?: null | string;
}

export interface AssistantSourceBasisItem {
  source_type: string;
  source_name?: null | string;
  page_id?: null | string;
  module_key?: null | string;
  title?: null | string;
  evidence: string;
}

export interface AssistantStructuredResponse {
  conversation_id: string;
  message_id: string;
  detected_language?: AssistantLanguageCode | null;
  response_language?: AssistantLanguageCode | null;
  answer: string;
  scope?: null | string;
  confidence?: AssistantConfidence;
  out_of_scope?: boolean;
  diagnosis?: AssistantDiagnosisItem[];
  links?: AssistantLink[];
  missing_permissions?: AssistantMissingPermission[];
  next_steps?: string[];
  tool_trace_id?: null | string;
  rag_trace_id?: null | string;
  source_basis?: AssistantSourceBasisItem[];
}

export interface AssistantMessage {
  id: string;
  role: 'assistant' | 'system_summary' | 'tool' | 'user';
  content: string;
  structured_payload?: AssistantStructuredResponse | null | Record<string, unknown>;
  detected_language?: null | string;
  response_language?: null | string;
  created_at?: string;
}

export type AssistantFeedbackRating = 'helpful' | 'not_helpful';

export interface AssistantFeedbackRequest {
  message_id: string;
  rating: AssistantFeedbackRating;
  comment?: null | string;
}

export interface AssistantFeedbackResponse {
  id: string;
  conversation_id: string;
  message_id: string;
  rating: AssistantFeedbackRating;
  created_at: string;
}

export interface AssistantConversation {
  id: string;
  title?: null | string;
  locale?: null | string;
  status?: string;
  last_route_name?: null | string;
  last_route_path?: null | string;
  messages?: AssistantMessage[];
  created_at?: string;
  updated_at?: string;
}

export interface AssistantPageHelpField {
  field_key: string;
  label: string;
  required?: boolean;
  verified?: boolean;
}

export interface AssistantPageHelpFormSection {
  section_key: string;
  title: string;
  verified?: boolean;
  fields?: AssistantPageHelpField[];
}

export interface AssistantPageHelpAction {
  action_key: string;
  label: string;
  label_status?: string;
  action_type?: string;
  selector?: null | string;
  test_id?: null | string;
  location?: null | string;
  required_permissions?: string[];
  opens?: null | string;
  result?: null | string;
  verified?: boolean;
  allowed?: boolean;
}

export interface AssistantPageHelpManifest {
  page_id: string;
  page_title: string;
  route_name?: null | string;
  path_template?: null | string;
  module_key: string;
  language_code?: null | string;
  source_status?: string;
  page_purpose?: null | string;
  workflow_keys?: string[];
  api_families?: string[];
  actions?: AssistantPageHelpAction[];
  form_sections?: AssistantPageHelpFormSection[];
  source_basis?: Array<{
    source_type: string;
    source_name?: null | string;
    page_id?: null | string;
    module_key?: null | string;
    evidence: string;
  }>;
}

interface AssistantApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    message_key?: string;
  };
}

export class AssistantApiError extends Error {
  code: string;
  messageKey: string;
  status: number;

  constructor(status: number, code: string, messageKey: string) {
    super(messageKey);
    this.name = 'AssistantApiError';
    this.status = status;
    this.code = code;
    this.messageKey = messageKey;
  }
}

function getApiBaseUrl() {
  return import.meta.env.VITE_GLOB_API_URL || '/api';
}

async function readAssistantApiErrorPayload(
  response: Response,
): Promise<AssistantApiErrorPayload> {
  return (await response.json().catch(() => null)) as AssistantApiErrorPayload;
}

function buildAssistantApiError(
  status: number,
  payload?: AssistantApiErrorPayload | null,
) {
  return new AssistantApiError(
    status,
    payload?.error?.code || `HTTP_${status}`,
    payload?.error?.message_key || 'errors.platform.internal',
  );
}

async function assistantApiRequest<T>(
  path: string,
  options?: {
    body?: unknown;
    method?: string;
  },
): Promise<T> {
  const accessStore = useAccessStore();
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      method: options?.method ?? 'GET',
      headers: {
        Authorization: accessStore.accessToken
          ? `Bearer ${accessStore.accessToken}`
          : '',
        'Accept-Language': preferences.app.locale,
        'Content-Type': 'application/json',
      },
      body: options?.body == null ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new AssistantApiError(
      0,
      'platform.network_unavailable',
      'errors.platform.network_unavailable',
    );
  }

  if (!response.ok) {
    const payload = await readAssistantApiErrorPayload(response);
    throw buildAssistantApiError(response.status, payload);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export function normalizeAssistantApiError(error: unknown) {
  if (error instanceof AssistantApiError) {
    return {
      code: error.code,
      messageKey: error.messageKey,
      status: error.status,
    };
  }

  if (error instanceof TypeError) {
    return {
      code: 'platform.network_unavailable',
      messageKey: 'errors.platform.network_unavailable',
      status: 0,
    };
  }

  return {
    code: 'platform.unknown_error',
    messageKey: 'errors.platform.internal',
    status: 0,
  };
}

export function getAssistantCapabilities(): Promise<AssistantCapabilities> {
  return assistantApiRequest<AssistantCapabilities>('/assistant/capabilities');
}

export function getAssistantProviderStatus(): Promise<AssistantProviderStatus> {
  return assistantApiRequest<AssistantProviderStatus>('/assistant/provider/status');
}

export function getAssistantPageHelp(
  pageId: string,
  languageCode?: null | string,
): Promise<AssistantPageHelpManifest> {
  const query = languageCode ? `?language_code=${encodeURIComponent(languageCode)}` : '';
  return assistantApiRequest<AssistantPageHelpManifest>(`/assistant/page-help/${pageId}${query}`);
}

export function createAssistantConversation(payload: {
  initial_route?: AssistantRouteContext | null;
  locale?: null | string;
  title?: null | string;
}): Promise<AssistantConversation> {
  return assistantApiRequest<AssistantConversation>('/assistant/conversations', {
    body: payload,
    method: 'POST',
  });
}

export function getAssistantConversation(
  conversationId: string,
): Promise<AssistantConversation> {
  return assistantApiRequest<AssistantConversation>(
    `/assistant/conversations/${conversationId}`,
  );
}

export function sendAssistantMessage(
  conversationId: string,
  payload: {
    message: string;
    route_context?: AssistantRouteContext | null;
    client_context?: AssistantClientContext | null;
  },
): Promise<AssistantStructuredResponse> {
  return assistantApiRequest<AssistantStructuredResponse>(
    `/assistant/conversations/${conversationId}/messages`,
    {
      body: payload,
      method: 'POST',
    },
  );
}

export function submitAssistantFeedback(
  conversationId: string,
  payload: AssistantFeedbackRequest,
): Promise<AssistantFeedbackResponse> {
  return assistantApiRequest<AssistantFeedbackResponse>(
    `/assistant/conversations/${conversationId}/feedback`,
    {
      body: payload,
      method: 'POST',
    },
  );
}
