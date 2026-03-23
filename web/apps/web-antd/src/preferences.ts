import { defineOverridesPreferences } from '@vben/preferences';

/**
 * @description 项目配置文件
 * 只需要覆盖项目中的一部分配置，不需要的配置不用覆盖，会自动使用默认配置
 * !!! 更改配置后请清空缓存，否则可能不生效
 */
export const overridesPreferences = defineOverridesPreferences({
  app: {
    contentPadding: 0,
    contentPaddingBottom: 0,
    contentPaddingLeft: 0,
    contentPaddingRight: 0,
    contentPaddingTop: 0,
    defaultHomePath: '/admin/dashboard',
    locale: 'de-DE',
    layout: 'mixed-nav',
    name: 'SicherPlan',
  },
  breadcrumb: {
    enable: true,
    showHome: false,
    showIcon: false,
  },
  header: {
    height: 56,
    menuAlign: 'start',
  },
  logo: {
    enable: true,
    source: '',
    sourceDark: '',
  },
  navigation: {
    accordion: true,
    split: true,
    styleType: 'rounded',
  },
  sidebar: {
    autoActivateChild: true,
    expandOnHover: false,
    width: 248,
  },
  tabbar: {
    enable: true,
    showMaximize: false,
    styleType: 'chrome',
  },
  theme: {
    colorPrimary: 'rgb(40, 170, 170)',
    mode: 'light',
    semiDarkSidebar: true,
    semiDarkSidebarSub: true,
  },
});
