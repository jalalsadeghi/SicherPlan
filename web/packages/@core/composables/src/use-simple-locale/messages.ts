export type Locale = 'de-DE' | 'en-US';

export const messages: Record<Locale, Record<string, string>> = {
  'de-DE': {
    cancel: 'Abbrechen',
    collapse: 'Einklappen',
    confirm: 'Bestätigen',
    expand: 'Ausklappen',
    prompt: 'Hinweis',
    reset: 'Zurücksetzen',
    submit: 'Absenden',
  },
  'en-US': {
    cancel: 'Cancel',
    collapse: 'Collapse',
    confirm: 'Confirm',
    expand: 'Expand',
    prompt: 'Prompt',
    reset: 'Reset',
    submit: 'Submit',
  },
};

export const getMessages = (locale: Locale) => messages[locale];
