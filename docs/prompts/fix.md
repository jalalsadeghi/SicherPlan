Please update the SicherPlan web admin page for Platform Admin tenant user management.

Context:
- Route: /admin/iam/users
- Current page file: web/apps/web-antd/src/views/sicherplan/tenant-users/index.vue
- Related API client: web/apps/web-antd/src/api/sicherplan/tenant-users.ts
- Related i18n files:
  - web/apps/web-antd/src/locales/langs/en-US/sicherplan.json
  - web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json
- Reusable UI component:
  - web/apps/web-antd/src/components/sicherplan/section-header.vue

Goal:
The page currently does not expose the “create tenant admin user / set username + temporary password” action in a sufficiently visible and context-aware place for Platform Admins. Improve the UX so that creating a tenant-scoped login for a selected tenant is obvious and easy.

What to implement:
1. In the “Tenant and filter” card, add a prominent primary action button in the header area using the existing SectionHeader action slot.
2. The button should be something like:
   - EN: “Create tenant admin”
   - DE equivalent in i18n
3. Clicking that button must open the existing create modal. Reuse the current modal state and submit logic if possible. Do not create a second parallel create flow unless absolutely necessary.
4. Keep the action context-aware:
   - The button should be disabled if no tenant is selected.
   - The modal should clearly show which tenant is currently selected (for example, a small info alert or read-only summary at the top such as “Creating account for: <tenant name> (<tenant code>)”).
5. Keep the current create fields and backend integration:
   - username
   - full_name
   - email
   - locale
   - status
   - temporary_password
   - timezone if already part of the form/state
   - use the existing createTenantUser API
6. Keep the existing password reset flow unchanged.
7. Preserve the current generated temporary password behavior after successful creation.
8. Move or duplicate the “Refresh list” action to the same local action area near the tenant selector, so the main operational actions are grouped together. Avoid a confusing duplicated primary action in two unrelated places.
9. Improve the empty-state behavior:
   - If the selected tenant has no tenant_admin users yet, show a clearer empty-state hint or CTA near the table area that encourages creating the first tenant admin.
   - Do this with the existing Ant Design / SicherPlan visual language, not a new design pattern.
10. Keep the page responsive and aligned with the existing SicherPlan admin page structure and styling.
11. Use i18n keys instead of hardcoded user-facing strings.
12. Do not change backend contracts or IAM business rules. This is a web UX improvement, not a domain-model change.

Important implementation notes:
- The page already contains create logic and a create modal. The problem is discoverability and placement, not missing backend functionality.
- Prefer a single clear primary action near tenant selection instead of a generic action card far from the tenant context.
- Keep the implementation simple, clean, and consistent with the rest of the module pages.

Acceptance criteria:
- On /admin/iam/users, Platform Admin can immediately see a “Create tenant admin” button near tenant selection.
- Clicking it opens a modal dialog.
- The dialog makes the selected tenant explicit.
- Creating a user still calls the existing API and returns/shows the generated temporary password as before.
- No backend API changes are introduced.
- EN/DE translations are added/updated.
- The page remains responsive and visually consistent.

Please make the code changes directly in the appropriate files and then summarize:
1. which files you changed,
2. what UX changed,
3. whether any i18n keys were added,
4. whether any existing action buttons were moved or removed.