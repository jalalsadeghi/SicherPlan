import type { UserInfo } from '@vben/types';

interface SicherPlanRoleScope {
  role_key: string;
}

interface SicherPlanUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  roles: SicherPlanRoleScope[];
}

interface SicherPlanCurrentSessionResponse {
  user: SicherPlanUser;
}

function extractRoleKeys(roles: SicherPlanRoleScope[]): string[] {
  return [...new Set(roles.map((role) => role.role_key))];
}

function resolveHomePath(roleKeys: string[]): string {
  if (roleKeys.includes('customer_user')) {
    return '/portal/customer';
  }
  return '/admin/core';
}

function mapSicherPlanUserToVbenUser(
  user: SicherPlanUser,
  token: string,
): UserInfo {
  const roles = extractRoleKeys(user.roles);
  return {
    avatar: '',
    desc: user.email,
    homePath: resolveHomePath(roles),
    realName: user.full_name,
    roles,
    token,
    userId: user.id,
    username: user.username,
  };
}

function mapCurrentSessionToVbenUser(
  response: SicherPlanCurrentSessionResponse,
  token: string,
): UserInfo {
  return mapSicherPlanUserToVbenUser(response.user, token);
}

export {
  extractRoleKeys,
  mapCurrentSessionToVbenUser,
  mapSicherPlanUserToVbenUser,
  resolveHomePath,
};
export type {
  SicherPlanCurrentSessionResponse,
  SicherPlanRoleScope,
  SicherPlanUser,
};
