# Task: Reorganize the dashboard into two rows and correct the card styling

## Objective
Fix the dashboard layout so it follows this exact structure:

### Row 1
- **Daily Control for SicherPlan**
- **Quick Actions**

### Row 2
- **Date**
- **Tenants**
- **Active Tenants**
- **Admin Surfaces**

The current layout is incorrect and must be restructured.

---

## Required Layout

### First row
The first row must contain exactly **2 cards**:
1. `Daily Control for SicherPlan`
2. `Quick Actions`

These two cards should sit side by side on large screens.

### Second row
The second row must contain exactly **4 cards**:
1. `Date`
2. `Tenants`
3. `Active Tenants`
4. `Admin Surfaces`

These four cards should appear in one row on large screens.

### Responsive behavior
- large screens: 2 cards in row 1, 4 cards in row 2
- medium screens: wrap cleanly without broken spacing
- small screens: stack naturally

---

## Required Visual Style

### Plain background cards
The following cards must use a **plain background**:
- `Daily Control for SicherPlan`
- `Quick Actions`
- `Tenants`
- `Active Tenants`
- `Admin Surfaces`

Plain background means:
- no strong gradient
- no tinted feature-panel style
- no decorative background waves
- use the normal card style already available in the project

### Date card
The `Date` card must use the platform’s **primary built-in color** as its background.

Rules:
- do not invent a new color outside the existing design system
- use the project’s current primary theme color
- keep text readable on top of that background
- the Date card should be visually stronger than the other cards

---

## Card Content Rules

### Daily Control for SicherPlan
- plain card background
- title and short descriptive text
- optional small status chips/badges if already supported
- no gradient hero style
- should feel like a high-level summary card, not a promotional banner

### Quick Actions
- plain card background
- title + short description
- action buttons/links inside the card
- should sit next to “Daily Control for SicherPlan” in row 1
- buttons should remain inside the existing design system

### Date
- prominent date presentation
- uses primary built-in background color
- includes date-related information such as:
  - day
  - month/year
  - optional weekday
- may include small supporting actions like `Today` / `Overview` if already present

### Tenants
- plain card background
- number/value
- short subtitle
- icon in top-right corner

### Active Tenants
- plain card background
- number/value
- short subtitle
- icon in top-right corner

### Admin Surfaces
- plain card background
- number/value
- short subtitle
- icon in top-right corner

---

## Icon Requirement
Each card in the **second row** must display a relevant icon in its **top-right corner**.

This applies to:
- Date
- Tenants
- Active Tenants
- Admin Surfaces

Rules:
- use existing icon system already used in the project
- keep icon styling consistent with the dashboard
- icon should be visually balanced and not oversized
- if existing dashboard stat-card pattern has icon badges, reuse that pattern

---

## Implementation Requirements

### Reuse existing project styles
Reuse:
- current card components
- existing spacing system
- existing icon system
- existing button styles
- current theme tokens
- current dashboard/page wrapper styles

### Do not modify global styles
Do **not** modify:
- base CSS
- global CSS
- root theme files
- shared global card styles
- core theme configuration

If additional styling is needed, keep it:
- dashboard-local
- component-scoped
- minimal

### Do not create a second dashboard system
This must be an update to the existing dashboard implementation, not a parallel custom page.

---

## Suggested Technical Direction
Please inspect the current dashboard component and:

1. remove the incorrect current top-card arrangement
2. create a clean two-row card grid
3. move `Quick Actions` into row 1
4. move `Date`, `Tenants`, `Active Tenants`, and `Admin Surfaces` into row 2
5. replace the current gradient/feature styling of `Daily Control for SicherPlan` with a plain card style
6. apply the platform primary built-in background only to the `Date` card
7. add top-right icons to all second-row cards

---

## Deliverables
Please provide:

1. short summary of the layout changes
2. short summary of the styling changes
3. files changed
4. confirmation that no global/base/theme files were modified

Then apply the changes directly in the repository.

---

## Acceptance Criteria
This task is complete only if:

1. the dashboard has exactly two main rows of cards
2. row 1 contains only:
   - Daily Control for SicherPlan
   - Quick Actions
3. row 2 contains only:
   - Date
   - Tenants
   - Active Tenants
   - Admin Surfaces
4. Daily Control for SicherPlan uses a plain card background
5. Quick Actions uses a plain card background
6. Date uses the platform’s primary built-in background color
7. each second-row card has a relevant top-right icon
8. the layout is responsive and visually clean
9. no global/base/theme styles were modified