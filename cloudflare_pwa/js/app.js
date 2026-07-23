// App bootstrap: nav rail + hash-routed workflow views, command palette,
// install prompt, and service-worker update toast. Vue 3 Options API on the
// vendored global build (window.Vue).

import { store, loadStore, applyTheme, setLang } from './store.js';
import { t, LANGUAGES } from './i18n.js';
import { pushToast } from './toast.js';
import { Icon } from './icons.js';
import {
  JsonTreeNode,
  XmlTreeNode,
  CommandPalette,
  ToastHost,
} from './components/shared.js';
import { ConvertWorkflow } from './components/convert.js';
import { BulkWorkflow } from './components/bulk.js';
import { BuilderWorkflow } from './components/builder.js';
import { PassportWorkflow } from './components/passport.js';
import { ExploreWorkflow } from './components/explore.js';

const { createApp } = window.Vue;

const ROUTES = {
  convert: { component: 'ConvertWorkflow', icon: 'convert', key: 'nav.convert' },
  bulk: { component: 'BulkWorkflow', icon: 'bulk', key: 'nav.bulk' },
  builder: { component: 'BuilderWorkflow', icon: 'builder', key: 'nav.builder' },
  passport: { component: 'PassportWorkflow', icon: 'passport', key: 'nav.passport' },
  explore: { component: 'ExploreWorkflow', icon: 'explore', key: 'nav.explore' },
};

function viewFromHash() {
  const view = location.hash.replace(/^#\/?/, '').split('?')[0];
  return ROUTES[view] ? view : 'convert';
}

let deferredInstallPrompt = null;

const App = {
  components: {
    ConvertWorkflow,
    BulkWorkflow,
    BuilderWorkflow,
    PassportWorkflow,
    ExploreWorkflow,
    CommandPalette,
    ToastHost,
  },
  data() {
    return {
      store,
      view: viewFromHash(),
      routes: ROUTES,
      languages: LANGUAGES,
      paletteOpen: false,
      canInstall: false,
    };
  },
  computed: {
    currentComponent() {
      return ROUTES[this.view].component;
    },
    themeLabel() {
      return { auto: 'Auto', light: 'Light', dark: 'Dark' }[store.theme] || 'Auto';
    },
    commands() {
      const cmds = Object.entries(ROUTES).map(([key, route]) => ({
        id: `go-${key}`,
        label: `Go to ${this.t(route.key)}`,
        hint: key,
        run: () => this.go(key),
      }));
      cmds.push({ id: 'theme', label: `Theme: ${this.themeLabel} → next`, run: () => this.cycleTheme() });
      if (this.canInstall) cmds.push({ id: 'install', label: 'Install app', run: () => this.install() });
      return cmds;
    },
  },
  methods: {
    t,
    go(view) {
      this.view = view;
      location.hash = `#/${view}`;
    },
    cycleTheme() {
      const order = ['auto', 'light', 'dark'];
      const index = order.indexOf(store.theme);
      applyTheme(order[(index + 1) % order.length]);
    },
    onLang(event) {
      setLang(event.target.value);
    },
    async install() {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      this.canInstall = false;
    },
    onKeydown(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        this.paletteOpen = !this.paletteOpen;
      }
    },
  },
  mounted() {
    window.addEventListener('hashchange', () => {
      this.view = viewFromHash();
    });
    window.addEventListener('keydown', this.onKeydown);
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      deferredInstallPrompt = event;
      this.canInstall = true;
    });
  },
  template: `
  <div class="app">
    <a href="#main" class="skip-link">{{ t('app.skip') }}</a>
    <aside class="nav">
      <div class="nav__brand">
        <div class="nav__logo">GS1</div>
        <div>
          <div class="nav__title">{{ t('app.title') }}</div>
          <div class="nav__sub">{{ t('app.subtitle') }}</div>
        </div>
      </div>
      <nav class="nav__links" aria-label="Workflows">
        <button v-for="(route, key) in routes" :key="key"
          class="nav__link" :class="{ 'nav__link--active': view === key }"
          :aria-current="view === key ? 'page' : null" @click="go(key)">
          <span class="nav__icon"><app-icon :name="route.icon" /></span> {{ t(route.key) }}
        </button>
      </nav>
      <div class="nav__foot">
        <button v-if="canInstall" class="nav__install" type="button" @click="install"><app-icon name="install" :size="16" /> {{ t('nav.install') }}</button>
        <button class="nav__theme" type="button" @click="cycleTheme"><app-icon name="theme" :size="16" /> Theme: {{ themeLabel }}</button>
        <label class="nav__lang">
          <span class="visually-hidden">Language</span>
          <select class="input input--sm" :value="store.lang" @change="onLang">
            <option v-for="l in languages" :key="l.code" :value="l.code">{{ l.label }}</option>
          </select>
        </label>
        <p class="nav__note">{{ t('app.offline') }}</p>
      </div>
    </aside>

    <main id="main" class="main">
      <div v-if="store.error" class="alert alert--error">Failed to load app data: {{ store.error }}</div>
      <div v-else-if="!store.ready" class="loading">Loading vocabulary and mapping data…</div>
      <transition v-else name="view" mode="out-in">
        <component :is="currentComponent" :key="view" />
      </transition>
      <footer class="appfooter" v-if="store.ready">
        <span><app-icon name="check" :size="14" /> Offline · client-side only</span>
        <span class="appfooter__dot">·</span>
        <span>GS1 Web Vocabulary 1.17</span>
        <span class="appfooter__dot">·</span>
        <span>Output verified byte-for-byte against the reference converter</span>
      </footer>
    </main>

    <command-palette :open="paletteOpen" :commands="commands" @close="paletteOpen = false" />
    <toast-host />
  </div>
  `,
};

applyTheme(store.theme);
loadStore();

const app = createApp(App);
// Register globally: the recursive tree nodes (self-reference by name) + the icon.
app.component('JsonTreeNode', JsonTreeNode);
app.component('XmlTreeNode', XmlTreeNode);
app.component('AppIcon', Icon);
app.mount('#app');

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('sw.js')
      .then((registration) => {
        registration.addEventListener('updatefound', () => {
          const worker = registration.installing;
          if (!worker) return;
          worker.addEventListener('statechange', () => {
            if (worker.state === 'installed' && navigator.serviceWorker.controller) {
              pushToast('A new version is available.', {
                sticky: true,
                actionLabel: 'Reload',
                action: () => {
                  worker.postMessage({ type: 'SKIP_WAITING' });
                },
              });
            }
          });
        });
      })
      .catch(() => {
        /* offline install is best-effort */
      });
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
  });
}
