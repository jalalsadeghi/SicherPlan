export type AssistantDockSide =
  | 'bottom-left'
  | 'bottom-right'
  | 'custom'
  | 'top-left'
  | 'top-right';

export interface AssistantFloatingPosition {
  x: number;
  y: number;
  dockSide: AssistantDockSide;
  userPinned: boolean;
  lastMovedBy: 'system' | 'user';
  updatedAt: string;
}

export interface AssistantLauncherMetrics {
  height: number;
  width: number;
}

export interface AssistantViewportMetrics {
  height: number;
  width: number;
}

export const ASSISTANT_FLOATING_POSITION_STORAGE_KEY =
  'sicherplan.assistant.floatingPosition.v1';
export const ASSISTANT_FLOATING_HINT_STORAGE_KEY =
  'sicherplan.assistant.floatingHintDismissed.v1';
export const ASSISTANT_FLOATING_SAFE_MARGIN = 12;
export const ASSISTANT_FLOATING_DESKTOP_MARGIN = 16;
export const ASSISTANT_FLOATING_MOBILE_MARGIN = 8;
export const ASSISTANT_FLOATING_MOBILE_BREAKPOINT = 640;
export const ASSISTANT_FLOATING_FALLBACK_LAUNCHER_WIDTH = 220;
export const ASSISTANT_FLOATING_FALLBACK_LAUNCHER_HEIGHT = 48;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function resolveNowIsoString() {
  return new Date().toISOString();
}

export function getAssistantViewportMetrics(): AssistantViewportMetrics {
  if (typeof window === 'undefined') {
    return {
      height: 768,
      width: 1366,
    };
  }
  return {
    height: window.innerHeight,
    width: window.innerWidth,
  };
}

export function normalizeAssistantLauncherMetrics(
  metrics?: null | Partial<AssistantLauncherMetrics>,
): AssistantLauncherMetrics {
  return {
    height:
      metrics && isFiniteNumber(metrics.height) && metrics.height > 0
        ? metrics.height
        : ASSISTANT_FLOATING_FALLBACK_LAUNCHER_HEIGHT,
    width:
      metrics && isFiniteNumber(metrics.width) && metrics.width > 0
        ? metrics.width
        : ASSISTANT_FLOATING_FALLBACK_LAUNCHER_WIDTH,
  };
}

export function isAssistantMobileViewport(
  viewport: AssistantViewportMetrics,
): boolean {
  return viewport.width <= ASSISTANT_FLOATING_MOBILE_BREAKPOINT;
}

export function resolveAssistantDefaultFloatingPosition(
  viewport: AssistantViewportMetrics,
  launcherMetrics?: null | Partial<AssistantLauncherMetrics>,
): AssistantFloatingPosition {
  const launcher = normalizeAssistantLauncherMetrics(launcherMetrics);
  const isMobile = isAssistantMobileViewport(viewport);
  const margin = isMobile
    ? ASSISTANT_FLOATING_MOBILE_MARGIN
    : ASSISTANT_FLOATING_DESKTOP_MARGIN;
  return {
    dockSide: 'bottom-right',
    lastMovedBy: 'system',
    updatedAt: resolveNowIsoString(),
    userPinned: false,
    x: Math.max(
      margin,
      viewport.width - launcher.width - margin,
    ),
    y: Math.max(
      margin,
      viewport.height - launcher.height - margin,
    ),
  };
}

export function clampAssistantFloatingPosition(
  position: AssistantFloatingPosition,
  viewport: AssistantViewportMetrics,
  launcherMetrics?: null | Partial<AssistantLauncherMetrics>,
): AssistantFloatingPosition {
  const launcher = normalizeAssistantLauncherMetrics(launcherMetrics);
  const isMobile = isAssistantMobileViewport(viewport);
  const maxX = Math.max(
    ASSISTANT_FLOATING_SAFE_MARGIN,
    viewport.width - launcher.width - ASSISTANT_FLOATING_SAFE_MARGIN,
  );
  const maxY = Math.max(
    ASSISTANT_FLOATING_SAFE_MARGIN,
    viewport.height - launcher.height - ASSISTANT_FLOATING_SAFE_MARGIN,
  );
  const clampedX = Math.min(
    Math.max(position.x, ASSISTANT_FLOATING_SAFE_MARGIN),
    maxX,
  );
  const clampedY = isMobile
    ? resolveAssistantDefaultFloatingPosition(viewport, launcher).y
    : Math.min(Math.max(position.y, ASSISTANT_FLOATING_SAFE_MARGIN), maxY);
  return {
    ...position,
    x: clampedX,
    y: clampedY,
  };
}

export function snapAssistantFloatingPosition(
  position: AssistantFloatingPosition,
  viewport: AssistantViewportMetrics,
  launcherMetrics?: null | Partial<AssistantLauncherMetrics>,
): AssistantFloatingPosition {
  const launcher = normalizeAssistantLauncherMetrics(launcherMetrics);
  const isMobile = isAssistantMobileViewport(viewport);
  const clamped = clampAssistantFloatingPosition(position, viewport, launcher);
  const launcherCenterX = clamped.x + launcher.width / 2;
  const launcherCenterY = clamped.y + launcher.height / 2;
  const preferLeft = launcherCenterX <= viewport.width / 2;
  const useTopDock = !isMobile && launcherCenterY <= viewport.height / 2;
  const x = preferLeft
    ? ASSISTANT_FLOATING_SAFE_MARGIN
    : Math.max(
        ASSISTANT_FLOATING_SAFE_MARGIN,
        viewport.width - launcher.width - ASSISTANT_FLOATING_SAFE_MARGIN,
      );
  const y = isMobile
    ? resolveAssistantDefaultFloatingPosition(viewport, launcher).y
    : clamped.y;
  const dockSide: AssistantDockSide = preferLeft
    ? (useTopDock ? 'top-left' : 'bottom-left')
    : (useTopDock ? 'top-right' : 'bottom-right');
  return {
    ...clamped,
    dockSide,
    lastMovedBy: 'user',
    updatedAt: resolveNowIsoString(),
    userPinned: true,
    x,
    y,
  };
}

export function readAssistantFloatingPosition(): AssistantFloatingPosition | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const rawValue = window.localStorage.getItem(
    ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
  );
  if (!rawValue) {
    return null;
  }
  try {
    const parsed = JSON.parse(rawValue) as Partial<AssistantFloatingPosition>;
    if (
      !isFiniteNumber(parsed.x)
      || !isFiniteNumber(parsed.y)
      || typeof parsed.dockSide !== 'string'
      || typeof parsed.userPinned !== 'boolean'
      || (parsed.lastMovedBy !== 'system' && parsed.lastMovedBy !== 'user')
      || typeof parsed.updatedAt !== 'string'
    ) {
      return null;
    }
    return {
      dockSide: parsed.dockSide as AssistantDockSide,
      lastMovedBy: parsed.lastMovedBy,
      updatedAt: parsed.updatedAt,
      userPinned: parsed.userPinned,
      x: parsed.x,
      y: parsed.y,
    };
  } catch {
    return null;
  }
}

export function persistAssistantFloatingPosition(
  position: AssistantFloatingPosition,
) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(
    ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
    JSON.stringify(position),
  );
}

export function clearAssistantFloatingPosition() {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem(ASSISTANT_FLOATING_POSITION_STORAGE_KEY);
}

export function readAssistantFloatingHintDismissed() {
  if (typeof window === 'undefined') {
    return false;
  }
  return window.localStorage.getItem(ASSISTANT_FLOATING_HINT_STORAGE_KEY) === '1';
}

export function persistAssistantFloatingHintDismissed(dismissed = true) {
  if (typeof window === 'undefined') {
    return;
  }
  if (dismissed) {
    window.localStorage.setItem(ASSISTANT_FLOATING_HINT_STORAGE_KEY, '1');
    return;
  }
  window.localStorage.removeItem(ASSISTANT_FLOATING_HINT_STORAGE_KEY);
}
