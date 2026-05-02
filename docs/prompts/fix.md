We need a small, UI-only refinement in the Order Workspace step navigation.

Context:
In the Customer detail > Orders flow, when the user enters the embedded order workspace (the 6-step flow shown at the top of the order workspace), the current step navigation renders as 6 separate step buttons/cards, each with a visible step number above the label.

Requested changes:
1. Remove the visible step number from every step.
   - Example: remove the small “1”, “2”, “3”, etc. shown above each step label.
   - Keep the step labels themselves unchanged:
     - Order details
     - Order scope & documents
     - Planning record
     - Planning documents
     - Shift plan
     - Series & exceptions

2. Change only the visual surface shape of the 6 step items so they look like connected/integrated arrow steps (chevron / interlocked breadcrumb-style arrows), similar to the provided visual reference.
   - Important: this is only a shape/layout styling change.
   - Do NOT change the current color system.
   - Do NOT change active/inactive/hover/selected color behavior.
   - Do NOT change click behavior, routing, step activation logic, disabled logic, or any workflow behavior.
   - Do NOT change the order of steps.
   - Do NOT change the text labels.
   - Do NOT change any backend/API/state contract.

Very important constraints:
- Keep the current interaction behavior exactly as-is.
- Keep current colors exactly as-is.
- Keep the current active-step logic exactly as-is.
- Keep responsiveness clean.
- Prefer a CSS-first solution with minimal template changes.
- If the step number is generated from data, remove it only from visible UI, without breaking internal logic.
- If needed, preserve accessibility with aria-labels, but do not show the visible step number in the UI.

Implementation guidance:
1. First identify the exact frontend component(s) responsible for rendering the order workspace step navigation.
2. Inspect whether the step items are rendered from a shared stepper component or a local order-workspace component.
3. Apply the smallest safe change.
4. Prefer using CSS and/or pseudo-elements (::before / ::after) or clip-path to create the arrow/chevron connected shape.
5. The shape should visually read as sequential connected steps, like a horizontal arrow-step progress strip.
6. Preserve current spacing, alignment, focus behavior, and responsive wrapping/fallback behavior.
7. Do not introduce visual regressions in the surrounding order workspace layout.

Please do the following before coding:
- Briefly state which file(s) you believe are impacted.
- Briefly explain the smallest safe implementation approach.
- Mention any risk of shared-component side effects.

Acceptance criteria:
- The visible step numbers are gone.
- The 6 steps visually look like connected arrow/chevron steps.
- The colors remain unchanged from the current implementation.
- Active/inactive visual state logic remains unchanged except for the new shape.
- Clicking a step behaves exactly as before.
- No route/state/API/backend changes.
- No unrelated UI changes.

After implementation:
- List changed files.
- Summarize exactly what changed.
- Run the most relevant frontend tests if available.
- If no exact test exists, at least perform a focused sanity check on the order workspace UI code path.