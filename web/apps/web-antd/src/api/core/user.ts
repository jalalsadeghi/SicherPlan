import type { UserInfo } from '@vben/types';

import { useAccessStore } from '@vben/stores';

import { getCurrentSessionApi } from './auth';
import { mapCurrentSessionToVbenUser } from './auth.mappers';

/**
 * 获取用户信息
 */
export async function getUserInfoApi() {
  const accessStore = useAccessStore();
  const response = await getCurrentSessionApi();
  return mapCurrentSessionToVbenUser(
    response,
    accessStore.accessToken ?? '',
  ) as UserInfo;
}
