import { describe, expect, it } from 'vitest';

import {
  buildLauncherRect,
  findAssistantSafePosition,
  rectsIntersect,
  resolveAssistantAutoPlacement,
} from '../assistant-placement';

describe('assistant placement utility', () => {
  it('keeps bottom-right when no avoid zones exist', () => {
    const result = findAssistantSafePosition({
      avoidRects: [],
      launcherSize: { width: 220, height: 48 },
      margin: 12,
      preferredDock: 'bottom-right',
      viewport: { width: 1280, height: 720 },
    });

    expect(result.dockSide).toBe('bottom-right');
  });

  it('avoids a bottom-right action rect by choosing a different candidate', () => {
    const result = findAssistantSafePosition({
      avoidRects: [
        {
          top: 620,
          left: 980,
          right: 1270,
          bottom: 710,
          width: 290,
          height: 90,
        },
      ],
      launcherSize: { width: 220, height: 48 },
      margin: 12,
      preferredDock: 'bottom-right',
      viewport: { width: 1280, height: 720 },
    });

    expect(result.dockSide).not.toBe('bottom-right');
  });

  it('respects user-pinned positions even if they overlap avoid zones', () => {
    const result = resolveAssistantAutoPlacement({
      avoidRects: [
        {
          top: 620,
          left: 980,
          right: 1270,
          bottom: 710,
          width: 290,
          height: 90,
        },
      ],
      launcherSize: { width: 220, height: 48 },
      position: {
        x: 1030,
        y: 640,
        dockSide: 'bottom-right',
        userPinned: true,
        lastMovedBy: 'user',
        updatedAt: '2026-05-02T10:00:00.000Z',
      },
      viewport: { width: 1280, height: 720 },
    });

    expect(result.autoMoved).toBe(false);
    expect(result.position.x).toBe(1030);
  });

  it('clamps mobile positions inside the viewport', () => {
    const result = resolveAssistantAutoPlacement({
      avoidRects: [],
      launcherSize: { width: 220, height: 48 },
      position: {
        x: 500,
        y: 900,
        dockSide: 'bottom-right',
        userPinned: false,
        lastMovedBy: 'system',
        updatedAt: '2026-05-02T10:00:00.000Z',
      },
      viewport: { width: 360, height: 640 },
    });

    expect(result.position.x).toBeGreaterThanOrEqual(12);
    expect(result.position.y).toBeGreaterThanOrEqual(12);
    expect(result.position.x).toBeLessThanOrEqual(360);
  });

  it('detects intersection with avoid rectangles correctly', () => {
    const launcherRect = buildLauncherRect(
      { x: 1020, y: 640 },
      { width: 220, height: 48 },
    );

    expect(
      rectsIntersect(launcherRect, {
        top: 620,
        left: 980,
        right: 1270,
        bottom: 710,
        width: 290,
        height: 90,
      }),
    ).toBe(true);
  });
});
