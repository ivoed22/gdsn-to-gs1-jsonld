// UI i18n scaffold. English ships now; the structure (strings.<lang> + t())
// supports adding nl/de/fr later without touching components. Components call
// t('key', 'English fallback'); the fallback renders if a key is missing, so
// partial translations never break the UI.

import { store } from './store.js';

export const LANGUAGES = [{ code: 'en', label: 'English' }];

const strings = {
  en: {
    'app.title': 'GDSN → JSON-LD',
    'app.subtitle': 'Web Vocabulary converter',
    'app.offline': 'Offline PWA · client-side only',
    'app.skip': 'Skip to main content',
    'nav.convert': 'Convert',
    'nav.bulk': 'Bulk',
    'nav.builder': 'Builder',
    'nav.passport': 'Passport',
    'nav.explore': 'Explore',
    'nav.install': 'Install app',
    'action.convert': 'Convert',
    'action.download': 'Download',
    'palette.placeholder': 'Type a command…',
    'update.available': 'A new version is available.',
    'update.reload': 'Reload',
  },
};

export function t(key, fallback) {
  const lang = (store && store.lang) || 'en';
  const table = strings[lang] || strings.en;
  if (key in table) return table[key];
  if (fallback !== undefined) return fallback;
  if (key in strings.en) return strings.en[key];
  return key;
}
