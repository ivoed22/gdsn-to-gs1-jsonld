// Service worker: precache the full app shell + data + vendor assets on install
// so the converter works fully offline and is installable. Cache-first, with a
// network fallback that also fills the cache for anything not precached.

const CACHE = 'gdsn-jsonld-v8';

const PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/styles.css',
  './vendor/vue.global.prod.js',
  './vendor/qrcode.min.js',
  './vendor/fflate.min.js',
  './vendor/fonts/inter-400.woff2',
  './vendor/fonts/inter-500.woff2',
  './vendor/fonts/inter-600.woff2',
  './vendor/fonts/inter-700.woff2',
  './vendor/fonts/spacegrotesk-500.woff2',
  './vendor/fonts/spacegrotesk-700.woff2',
  './vendor/fonts/jetbrainsmono-400.woff2',
  './vendor/fonts/jetbrainsmono-500.woff2',
  './js/icons.js',
  './icons/icon.svg',
  './icons/icon-maskable.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './js/app.js',
  './js/store.js',
  './js/i18n.js',
  './js/toast.js',
  './js/components/shared.js',
  './js/components/convert.js',
  './js/components/bulk.js',
  './js/components/builder.js',
  './js/components/passport.js',
  './js/components/explore.js',
  './js/core/transforms.js',
  './js/core/model.js',
  './js/core/xml.js',
  './js/core/mapping.js',
  './js/core/jsonld.js',
  './js/core/validator.js',
  './js/core/readiness.js',
  './js/core/digitallink.js',
  './js/core/builder.js',
  './js/core/reports.js',
  './js/core/zip.js',
  './js/core/xlsx.js',
  './js/core/passport.js',
  './js/core/jsonld_check.js',
  './js/core/suggestions.js',
  './data/mappings/mapping_mvp.json',
  './data/mappings/mapping_v0_2.json',
  './data/mappings/mapping_v0_3.json',
  './data/mappings/mapping_v0_4.json',
  './data/builder_manifest.json',
  './data/webvoc_properties.json',
  './data/webvoc_classes.json',
  './data/webvoc_individuals.json',
  './data/mapping_catalog.json',
  './data/mapping_suggestions_v0_1.json',
  './data/dpp_minimal.schema.json',
  './data/samples/example_product.xml',
  './data/samples/certified_product_with_documents.xml',
  './data/samples/food_product_full.xml',
  './data/samples/minimal_product.xml',
  './data/samples/partially_mapped_product.xml',
];

self.addEventListener('install', (event) => {
  // Don't auto-skipWaiting: wait for the user's "Reload" (message below), so an
  // update never yanks assets from under an in-progress session.
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)));
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

// Stale-while-revalidate: serve the cached copy immediately for offline speed,
// but refresh it from the network in the background so shipped updates propagate
// on the next load (cache-first alone would pin stale app code forever).
self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(request).then((cached) => {
        const network = fetch(request)
          .then((response) => {
            if (response && response.ok && response.type === 'basic') {
              cache.put(request, response.clone());
            }
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    )
  );
});
