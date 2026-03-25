import { initPreferences, preferences, updatePreferences } from '@vben/preferences';
import { unmountGlobalLoading } from '@vben/utils';

import { overridesPreferences } from './preferences';
import { APP_LOCALE_STORAGE_KEY } from './sicherplan-legacy/stores/locale';

const defaultLocale = overridesPreferences.app?.locale ?? 'de-DE';
const DEFAULT_VBEN_LOGO_SOURCE =
  'https://unpkg.com/@vbenjs/static-source@0.1.7/source/logo-v1.webp';
const SICHERPLAN_LIGHT_LOGO_SOURCE =
  overridesPreferences.logo?.source || '/branding/sicherplan-logo-512.png';
const SICHERPLAN_DARK_LOGO_SOURCE =
  overridesPreferences.logo?.sourceDark ||
  overridesPreferences.logo?.source ||
  '/branding/sicherplan-logo-dark-512.png';

function resolveBootstrapLocale() {
  if (typeof window === 'undefined') {
    return defaultLocale;
  }

  const storedLocale = window.localStorage.getItem(APP_LOCALE_STORAGE_KEY);
  switch (storedLocale) {
    case 'en':
    case 'en-US':
      return 'en-US';
    case 'de':
    case 'de-DE':
      return 'de-DE';
    default:
      return defaultLocale;
  }
}

function migrateLogoPreferences() {
  const currentSource = preferences.logo.source?.trim() ?? '';
  const currentSourceDark = preferences.logo.sourceDark?.trim() ?? '';
  const shouldRepairLogo =
    !currentSource ||
    currentSource === DEFAULT_VBEN_LOGO_SOURCE ||
    !currentSourceDark ||
    currentSourceDark === DEFAULT_VBEN_LOGO_SOURCE ||
    currentSourceDark === SICHERPLAN_LIGHT_LOGO_SOURCE;

  if (!shouldRepairLogo) {
    return;
  }

  updatePreferences({
    logo: {
      fit: 'contain',
      source: SICHERPLAN_LIGHT_LOGO_SOURCE,
      sourceDark: SICHERPLAN_DARK_LOGO_SOURCE,
    },
  });
}

/**
 * 应用初始化完成之后再进行页面加载渲染
 */
async function initApplication() {
  // name用于指定项目唯一标识
  // 用于区分不同项目的偏好设置以及存储数据的key前缀以及其他一些需要隔离的数据
  const env = import.meta.env.PROD ? 'prod' : 'dev';
  const appVersion = import.meta.env.VITE_APP_VERSION;
  const namespace = `${import.meta.env.VITE_APP_NAMESPACE}-${appVersion}-${env}`;

  // app偏好设置初始化
  await initPreferences({
    namespace,
    overrides: {
      ...overridesPreferences,
      app: {
        ...overridesPreferences.app,
        locale: resolveBootstrapLocale(),
      },
    },
  });

  migrateLogoPreferences();

  // 启动应用并挂载
  // vue应用主要逻辑及视图
  const { bootstrap } = await import('./bootstrap');
  await bootstrap(namespace);

  // 移除并销毁loading
  unmountGlobalLoading();
}

initApplication();
