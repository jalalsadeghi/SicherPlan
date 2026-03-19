export type AppRole =
  | "platform_admin"
  | "tenant_admin"
  | "dispatcher"
  | "accounting"
  | "controller_qm"
  | "customer_user"
  | "subcontractor_user";

export const roleLabelKeys: Record<AppRole, `role.${AppRole}`> = {
  platform_admin: "role.platform_admin",
  tenant_admin: "role.tenant_admin",
  dispatcher: "role.dispatcher",
  accounting: "role.accounting",
  controller_qm: "role.controller_qm",
  customer_user: "role.customer_user",
  subcontractor_user: "role.subcontractor_user",
};
