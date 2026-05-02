import type {
  AssistantDockSide,
  AssistantFloatingPosition,
  AssistantLauncherMetrics,
  AssistantViewportMetrics,
} from './assistant-floating';

import {
  ASSISTANT_FLOATING_SAFE_MARGIN,
  clampAssistantFloatingPosition,
  isAssistantMobileViewport,
  normalizeAssistantLauncherMetrics,
  resolveAssistantDefaultFloatingPosition,
} from './assistant-floating';

export interface RectLike {
  bottom: number;
  height: number;
  left: number;
  right: number;
  top: number;
  width: number;
}

export interface AssistantSafeAreaInsets {
  bottom: number;
  left: number;
  right: number;
  top: number;
}

export const ASSISTANT_AVOID_SELECTOR =
  '[data-assistant-avoid], .sp-assistant-avoid';

function parsePixelValue(value: string) {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function readAssistantSafeAreaInsets(): AssistantSafeAreaInsets {
  if (typeof document === 'undefined') {
    return { top: 0, right: 0, bottom: 0, left: 0 };
  }
  const styles = getComputedStyle(document.documentElement);
  return {
    bottom: parsePixelValue(styles.getPropertyValue('--sp-safe-area-bottom')),
    left: parsePixelValue(styles.getPropertyValue('--sp-safe-area-left')),
    right: parsePixelValue(styles.getPropertyValue('--sp-safe-area-right')),
    top: parsePixelValue(styles.getPropertyValue('--sp-safe-area-top')),
  };
}

export function rectsIntersect(a: RectLike, b: RectLike) {
  return !(
    a.right <= b.left
    || a.left >= b.right
    || a.bottom <= b.top
    || a.top >= b.bottom
  );
}

export function buildLauncherRect(
  position: Pick<AssistantFloatingPosition, 'x' | 'y'>,
  launcherSize: AssistantLauncherMetrics,
): RectLike {
  return {
    bottom: position.y + launcherSize.height,
    height: launcherSize.height,
    left: position.x,
    right: position.x + launcherSize.width,
    top: position.y,
    width: launcherSize.width,
  };
}

export function queryAssistantAvoidRects(): RectLike[] {
  if (typeof document === 'undefined') {
    return [];
  }
  return Array.from(document.querySelectorAll<HTMLElement>(ASSISTANT_AVOID_SELECTOR))
    .map((element) => element.getBoundingClientRect())
    .filter((rect) => rect.width > 0 && rect.height > 0)
    .map((rect) => ({
      bottom: rect.bottom,
      height: rect.height,
      left: rect.left,
      right: rect.right,
      top: rect.top,
      width: rect.width,
    }));
}

function resolveSafeMarginWithInsets(
  margin: number,
  insets: AssistantSafeAreaInsets,
) {
  return {
    bottom: margin + insets.bottom,
    left: margin + insets.left,
    right: margin + insets.right,
    top: margin + insets.top,
  };
}

function resolveCandidatePositions(options: {
  launcherSize: AssistantLauncherMetrics;
  margin: number;
  preferredDock: AssistantDockSide;
  safeAreaInsets: AssistantSafeAreaInsets;
  viewport: AssistantViewportMetrics;
}): Array<{ dockSide: AssistantDockSide; x: number; y: number }> {
  const { launcherSize, margin, preferredDock, safeAreaInsets, viewport } = options;
  const safeMargin = resolveSafeMarginWithInsets(margin, safeAreaInsets);
  const maxX = Math.max(
    safeMargin.left,
    viewport.width - launcherSize.width - safeMargin.right,
  );
  const maxY = Math.max(
    safeMargin.top,
    viewport.height - launcherSize.height - safeMargin.bottom,
  );
  const centeredY = Math.max(
    safeMargin.top,
    Math.min(
      maxY,
      Math.round((viewport.height - launcherSize.height) / 2),
    ),
  );
  const candidates = [
    { dockSide: preferredDock, x: maxX, y: maxY },
    { dockSide: 'bottom-left' as const, x: safeMargin.left, y: maxY },
    { dockSide: 'top-right' as const, x: maxX, y: safeMargin.top },
    { dockSide: 'top-left' as const, x: safeMargin.left, y: safeMargin.top },
    { dockSide: 'custom' as const, x: maxX, y: centeredY },
    { dockSide: 'custom' as const, x: safeMargin.left, y: centeredY },
  ];
  return candidates.filter(
    (candidate, index, array) =>
      index === array.findIndex((item) =>
        item.dockSide === candidate.dockSide
        && item.x === candidate.x
        && item.y === candidate.y,
      ),
  );
}

export function findAssistantSafePosition(options: {
  avoidRects: RectLike[];
  launcherSize: AssistantLauncherMetrics;
  margin: number;
  preferredDock: AssistantDockSide;
  safeAreaInsets?: AssistantSafeAreaInsets;
  viewport: AssistantViewportMetrics;
}): { dockSide: AssistantDockSide; x: number; y: number } {
  const safeAreaInsets = options.safeAreaInsets ?? {
    bottom: 0,
    left: 0,
    right: 0,
    top: 0,
  };
  const launcherSize = normalizeAssistantLauncherMetrics(options.launcherSize);
  const candidates = resolveCandidatePositions({
    launcherSize,
    margin: options.margin,
    preferredDock: options.preferredDock,
    safeAreaInsets,
    viewport: options.viewport,
  });

  for (const candidate of candidates) {
    const rect = buildLauncherRect(candidate, launcherSize);
    if (!options.avoidRects.some((avoidRect) => rectsIntersect(rect, avoidRect))) {
      return candidate;
    }
  }

  const fallback = resolveAssistantDefaultFloatingPosition(
    options.viewport,
    launcherSize,
  );
  return clampAssistantFloatingPosition(
    fallback,
    options.viewport,
    launcherSize,
  );
}

export function shouldAutoPlaceAssistant(options: {
  hasAvoidRects: boolean;
  overlapWithAvoidZone: boolean;
  position: AssistantFloatingPosition;
}) {
  if (!options.hasAvoidRects) {
    return options.position.lastMovedBy !== 'user' || !options.position.userPinned;
  }
  if (options.position.lastMovedBy === 'user' && options.position.userPinned) {
    return false;
  }
  return options.overlapWithAvoidZone || !options.position.userPinned;
}

export function resolveAssistantAutoPlacement(options: {
  avoidRects: RectLike[];
  launcherSize: AssistantLauncherMetrics;
  margin?: number;
  position: AssistantFloatingPosition;
  safeAreaInsets?: AssistantSafeAreaInsets;
  viewport: AssistantViewportMetrics;
}) {
  const launcherSize = normalizeAssistantLauncherMetrics(options.launcherSize);
  const clamped = clampAssistantFloatingPosition(
    options.position,
    options.viewport,
    launcherSize,
  );
  const currentRect = buildLauncherRect(clamped, launcherSize);
  const overlapWithAvoidZone = options.avoidRects.some((rect) =>
    rectsIntersect(currentRect, rect),
  );
  if (
    !shouldAutoPlaceAssistant({
      hasAvoidRects: options.avoidRects.length > 0,
      overlapWithAvoidZone,
      position: clamped,
    })
  ) {
    return {
      autoMoved: false,
      position: clamped,
    };
  }

  const preferredDock = isAssistantMobileViewport(options.viewport)
    ? (clamped.x <= options.viewport.width / 2 ? 'bottom-left' : 'bottom-right')
    : clamped.dockSide === 'custom'
      ? (clamped.x <= options.viewport.width / 2 ? 'bottom-left' : 'bottom-right')
      : clamped.dockSide;
  const safePosition = findAssistantSafePosition({
    avoidRects: options.avoidRects,
    launcherSize,
    margin: options.margin ?? ASSISTANT_FLOATING_SAFE_MARGIN,
    preferredDock,
    safeAreaInsets: options.safeAreaInsets,
    viewport: options.viewport,
  });
  const autoMoved =
    safePosition.x !== clamped.x
    || safePosition.y !== clamped.y
    || safePosition.dockSide !== clamped.dockSide;
  return {
    autoMoved,
    position: {
      ...clamped,
      ...safePosition,
      lastMovedBy: 'system' as const,
      updatedAt: new Date().toISOString(),
      userPinned: false,
    },
  };
}
