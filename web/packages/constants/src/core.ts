/**
 * @zh_CN 登录页面 url 地址
 */
export const LOGIN_PATH = '/auth/login';

export interface LanguageOption {
  label: string;
  value: 'de-DE' | 'en-US';
}

/**
 * Supported languages
 */
export const SUPPORT_LANGUAGES: LanguageOption[] = [
  {
    label: 'Deutsch',
    value: 'de-DE',
  },
  {
    label: 'English',
    value: 'en-US',
  },
];
