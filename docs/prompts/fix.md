You are working in the SicherPlan repository.

Bug:
In /admin/employees > existing employee > Overview, the left-side section navigation looks correct visually, but it still does not stay visible while scrolling down.

User-visible evidence:
- At the top of Overview, the left nav appears correctly.
- When scrolling down to lower sections such as Qualifications, Addresses, Notes, Documents, the left nav stays behind at the top and disappears from the viewport.
- The user needs the left nav to remain visible/floating on the left side at all scroll positions inside the Overview page.

Important:
The link styling is now acceptable. Do NOT redesign the nav visually again.
Focus only on making the nav actually stay visible while scrolling.

Primary file:
- web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue

Current latest-code facts to validate:
1. EmployeeAdminView.vue already has:
   - employee-admin-overview-onepage
   - employee-admin-overview-nav-shell
   - employee-admin-overview-nav
   - employee-admin-overview-nav__link
   - employee-admin-overview-content
   - employee-admin-overview-section-card
2. CSS already contains something like:
   .employee-admin-overview-nav-shell {
     position: sticky;
     top: var(--employee-overview-sticky-top, 6.5rem);
     max-height: calc(100vh - var(--employee-overview-sticky-top, 6.5rem) - 1rem);
     overflow-y: auto;
   }
3. There is already IntersectionObserver scroll-spy logic:
   - employeeOverviewSectionObserver
   - setupEmployeeOverviewSectionObserver()
   - activeOverviewSection
4. Despite this, real browser QA shows the nav does not stay in the viewport.
5. Therefore, simply adding `position: sticky` again is not enough.

Required diagnosis:
Before changing code, inspect the real rendered layout and answer:
1. What is the actual scroll container?
   - window/document?
   - Vben layout content container?
   - another internal scrollable element?
2. Which ancestor of `.employee-admin-overview-nav-shell` prevents sticky from working?
   Check for:
   - overflow: hidden / auto / scroll
   - transform / filter / perspective
   - contain / will-change
   - height constraints
   - nav being inside a parent that ends too early
3. Is `.employee-admin-overview-nav-shell` actually a sibling of `.employee-admin-overview-content`?
4. Does `.employee-admin-overview-onepage` span the full height of all sections?
5. Does the sticky top offset place the nav under the app header/tabbar correctly?
6. If CSS sticky cannot be made reliable in this app layout, implement a robust fixed-position fallback.

Implementation requirement:
Use the best and most reliable method after diagnosis.

Preferred path A — fix CSS sticky if possible:
1. Keep nav inside the left column of `.employee-admin-overview-onepage`.
2. Ensure the parent layout allows sticky:
   - no breaking overflow on relevant ancestors if safely adjustable
   - one-page wrapper spans full content height
   - nav shell is not nested inside only the first section
3. Keep:
   - desktop sticky left nav
   - mobile static/horizontal nav
4. Validate in real browser.

Fallback path B — implement controlled fixed-position behavior:
If CSS sticky is still unreliable because of the app/Vben scroll container, implement a JS-assisted sticky/floating fallback.

Add refs:
- overviewOnePageRef
- overviewNavShellRef
- overviewNavPlaceholderRef if needed

Add reactive state:
- overviewNavFixed = false
- overviewNavPinnedToBottom = false
- overviewNavStyle = computed/inline style object

Behavior:
1. On desktop width only, when Overview tab is active and the user scrolls:
   - measure overview container rect
   - measure nav width/height
   - use a top offset matching the app header/tabbar, for example 96px or computed from CSS variable
2. If overview container top is above stickyTop and overview container bottom is below nav bottom:
   - set nav to position: fixed
   - set top = stickyTop
   - set left = overview container left
   - set width = nav column width
   - keep z-index above content but below app header/dropdowns
3. If user scrolls beyond bottom of overview container:
   - pin nav to the bottom of the overview container
   - either use absolute positioning inside the onepage wrapper
   - or remove fixed and use a transform/absolute bottom placement
4. If user scrolls above the overview container:
   - nav returns to normal static position.
5. On resize:
   - recalculate left/width/top.
6. On tab switch away from Overview:
   - disable fixed mode and cleanup.
7. On unmount:
   - remove scroll/resize listeners.
8. Use requestAnimationFrame throttling for scroll calculations.
9. Do not cause layout jump:
   - keep nav column width reserved
   - if fixed removes nav from flow, use the nav shell itself in a reserved aside or add placeholder.
10. Do not apply this on mobile/tablet widths where layout becomes one column.

Suggested implementation details:
- Keep existing `.employee-admin-overview-nav-shell` visual styles.
- Add class modifiers:
  - employee-admin-overview-nav-shell--fixed
  - employee-admin-overview-nav-shell--pinned
- Or bind inline style:
  :style="overviewNavFloatingStyle"
- Add data-testid:
  - employee-overview-nav-floating-shell

Important:
Do not create global scroll behavior or global CSS hacks.
This must be scoped to Employee Overview only.

Scroll-spy:
1. Preserve existing IntersectionObserver active link behavior.
2. If scroll container is not window, set the IntersectionObserver root to the actual scroll container.
3. rootMargin must account for sticky/fixed top offset.
4. Active link must update on manual scroll.

Click behavior:
1. Clicking a nav link still calls scrollIntoView or scrollTo equivalent.
2. If using a custom scroll container, use container-aware scrolling.
3. activeOverviewSection updates immediately on click.

Responsive:
1. Desktop/wide:
   - nav floats/stays visible on the left.
2. Tablet/mobile:
   - nav becomes static or horizontally scrollable above content.
   - no fixed overlay covering fields.

Do not change:
- Dashboard tab
- Overview content sections
- all employee forms/actions
- permission logic
- create employee flow
- search/import/export
- dashboard photo upload
- employee calendar
- backend APIs

Expected final behavior:
1. Open /admin/employees.
2. Select existing employee.
3. Click Overview.
4. Scroll down to Qualifications, Addresses, Notes, Documents.
5. Left nav remains visible in the viewport.
6. Active nav link changes according to visible section.
7. Clicking a nav link scrolls to that section.
8. On mobile/narrow width, nav remains usable and does not cover content.