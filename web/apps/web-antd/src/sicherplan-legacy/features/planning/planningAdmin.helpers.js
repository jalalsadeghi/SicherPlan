export const PLANNING_PERMISSION_MATRIX = {
  platform_admin: ["planning.ops.read", "planning.ops.write"],
  tenant_admin: ["planning.ops.read", "planning.ops.write"],
  dispatcher: ["planning.ops.read", "planning.ops.write"],
  accounting: [],
  controller_qm: [],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export const PLANNING_ENTITY_OPTIONS = [
  "requirement_type",
  "equipment_item",
  "site",
  "event_venue",
  "trade_fair",
  "patrol_route",
];

export function hasPlanningPermission(role, permissionKey) {
  return (PLANNING_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function derivePlanningActionState(role, entityKey, selectedRecord) {
  const canRead = hasPlanningPermission(role, "planning.ops.read");
  const canWrite = hasPlanningPermission(role, "planning.ops.write");
  return {
    canRead,
    canWrite,
    canCreate: canWrite,
    canEdit: canWrite && !!selectedRecord,
    canImport: canWrite,
    canManageChildren: canWrite && !!selectedRecord && (entityKey === "trade_fair" || entityKey === "patrol_route"),
  };
}

export function mapPlanningApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.planning.requirement_type.not_found": "notFound",
    "errors.planning.equipment_item.not_found": "notFound",
    "errors.planning.site.not_found": "notFound",
    "errors.planning.event_venue.not_found": "notFound",
    "errors.planning.trade_fair.not_found": "notFound",
    "errors.planning.trade_fair_zone.not_found": "notFound",
    "errors.planning.patrol_route.not_found": "notFound",
    "errors.planning.patrol_checkpoint.not_found": "notFound",
    "errors.planning.requirement_type.duplicate_code": "duplicateCode",
    "errors.planning.equipment_item.duplicate_code": "duplicateCode",
    "errors.planning.site.duplicate_code": "duplicateCode",
    "errors.planning.event_venue.duplicate_code": "duplicateCode",
    "errors.planning.trade_fair.duplicate_code": "duplicateCode",
    "errors.planning.patrol_route.duplicate_code": "duplicateCode",
    "errors.planning.trade_fair_zone.duplicate_tuple": "duplicateChild",
    "errors.planning.patrol_checkpoint.duplicate_sequence": "duplicateChild",
    "errors.planning.patrol_checkpoint.duplicate_code": "duplicateChild",
    "errors.planning.requirement_type.stale_version": "staleVersion",
    "errors.planning.equipment_item.stale_version": "staleVersion",
    "errors.planning.site.stale_version": "staleVersion",
    "errors.planning.event_venue.stale_version": "staleVersion",
    "errors.planning.trade_fair.stale_version": "staleVersion",
    "errors.planning.trade_fair_zone.stale_version": "staleVersion",
    "errors.planning.patrol_route.stale_version": "staleVersion",
    "errors.planning.patrol_checkpoint.stale_version": "staleVersion",
    "errors.planning.import.invalid_headers": "invalidImportHeaders",
    "errors.planning.import.invalid_csv": "invalidImportCsv",
    "errors.planning.import.invalid_entity_key": "invalidImportEntity",
  };
  return messageMap[messageKey] ?? "error";
}

export function buildPlanningImportTemplate(entityKey) {
  const headers = {
    requirement_type: ["customer_id", "code", "label", "default_planning_mode_code", "description", "status"],
    equipment_item: ["customer_id", "code", "label", "unit_of_measure_code", "description", "status"],
    site: ["customer_id", "site_no", "name", "address_id", "timezone", "latitude", "longitude", "watchbook_enabled", "notes", "status"],
    event_venue: ["customer_id", "venue_no", "name", "address_id", "timezone", "latitude", "longitude", "notes", "status"],
    trade_fair: ["customer_id", "venue_id", "fair_no", "name", "address_id", "timezone", "latitude", "longitude", "start_date", "end_date", "notes", "status"],
    patrol_route: ["customer_id", "site_id", "meeting_address_id", "route_no", "name", "start_point_text", "end_point_text", "travel_policy_code", "notes", "status"],
  };
  return (headers[entityKey] ?? []).join(",");
}

export function formatPlanningCustomerOption(customer) {
  if (!customer || typeof customer !== "object") {
    return "";
  }

  const customerNumber = typeof customer.customer_number === "string" ? customer.customer_number.trim() : "";
  const name = typeof customer.name === "string" ? customer.name.trim() : "";
  return [customerNumber, name].filter(Boolean).join(" — ") || "";
}

export function formatPlanningAddressOption(addressLink) {
  if (!addressLink || typeof addressLink !== "object") {
    return "";
  }

  const address = addressLink.address;
  if (!address || typeof address !== "object") {
    return addressLink.address_id || "";
  }

  const parts = [
    address.street_line_1,
    [address.postal_code, address.city].filter(Boolean).join(" "),
    address.country_code,
  ].filter(Boolean);

  return parts.join(" · ") || addressLink.address_id || "";
}

export function filterPlanningCustomerOptions(customers, query) {
  const normalizedQuery = typeof query === "string" ? query.trim().toLocaleLowerCase() : "";
  if (!normalizedQuery) {
    return customers;
  }

  return customers.filter((customer) => {
    const label = formatPlanningCustomerOption(customer).toLocaleLowerCase();
    return label.includes(normalizedQuery);
  });
}

export function parseOptionalCoordinate(value) {
  if (value == null) {
    return null;
  }

  if (typeof value === "string" && !value.trim()) {
    return null;
  }

  const numericValue = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

export function resolveInitialMapCenter({
  fallback,
  customerCoordinates = null,
  customerGeocode = null,
  currentLatitude,
  currentLongitude,
}) {
  const parsedLatitude = parseOptionalCoordinate(currentLatitude);
  const parsedLongitude = parseOptionalCoordinate(currentLongitude);

  if (parsedLatitude != null && parsedLongitude != null) {
    return {
      lat: Number(parsedLatitude.toFixed(6)),
      lng: Number(parsedLongitude.toFixed(6)),
      source: "existing-record",
    };
  }

  if (customerCoordinates?.lat != null && customerCoordinates?.lng != null) {
    return {
      lat: Number(customerCoordinates.lat.toFixed(6)),
      lng: Number(customerCoordinates.lng.toFixed(6)),
      source: "customer-coordinates",
    };
  }

  if (customerGeocode?.lat != null && customerGeocode?.lng != null) {
    return {
      lat: Number(customerGeocode.lat.toFixed(6)),
      lng: Number(customerGeocode.lng.toFixed(6)),
      source: "customer-geocode",
    };
  }

  return {
    lat: Number(fallback.lat.toFixed(6)),
    lng: Number(fallback.lng.toFixed(6)),
    source: "fallback",
  };
}
