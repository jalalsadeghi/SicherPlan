import { ELEMENT_ID_MAIN_CONTENT } from '@vben-core/shared/constants';

function isScrollableElement(element: HTMLElement) {
  const style = window.getComputedStyle(element);
  const overflowY = style.overflowY;
  return /(auto|scroll|overlay)/.test(overflowY) && element.scrollHeight > element.clientHeight;
}

export function getRouteCacheScrollTarget(doc: Document = document): HTMLElement {
  const mainContent = doc.getElementById(ELEMENT_ID_MAIN_CONTENT);
  if (mainContent instanceof HTMLElement) {
    if (isScrollableElement(mainContent)) {
      return mainContent;
    }
    for (const element of mainContent.querySelectorAll<HTMLElement>('*')) {
      if (isScrollableElement(element)) {
        return element;
      }
    }
  }

  return (
    (doc.scrollingElement as HTMLElement | null) ??
    doc.documentElement ??
    doc.body
  );
}

export function readRouteCacheScrollTop(doc: Document = document) {
  return getRouteCacheScrollTarget(doc).scrollTop;
}

export function writeRouteCacheScrollTop(
  scrollTop: number,
  doc: Document = document,
) {
  const target = getRouteCacheScrollTarget(doc);
  target.scrollTop = scrollTop;
  if (target === doc.documentElement && doc.body && doc.body !== target) {
    doc.body.scrollTop = scrollTop;
  }
}
