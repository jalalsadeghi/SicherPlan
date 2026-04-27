export const ADMIN_MENU_RESELECT_EVENT = "sicherplan:admin-menu-reselect";

export interface AdminMenuReselectDetail {
  to: string;
}

export function dispatchAdminMenuReselect(to: string) {
  window.dispatchEvent(
    new CustomEvent<AdminMenuReselectDetail>(ADMIN_MENU_RESELECT_EVENT, {
      detail: { to },
    }),
  );
}
