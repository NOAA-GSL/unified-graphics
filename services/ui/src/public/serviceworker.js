const VERSION = "20230228"; // eslint-disable-line no-unused-vars

/**
 * Enable navigation preload if it's supported.
 *
 * This function is async so that it can be called in ExtendableEvent.waitUntil
 * during service worker activation. Navigation preload allows the browser to
 * make network requests in parallel with service worker start up so that if we
 * don't have the requested resource in the cache already, we get it sooner.
 */
async function enableNavigationPreload() {
  if (self.registration.navigationPreload) {
    await self.registration.navigationPreload.enable();
  }
}

self.addEventListener("activate", (event) => {
  event.waitUntil(enableNavigationPreload());
});

self.addEventListener("install", () => {
  // Don't wait to activate the new service worker in open tabs.
  self.skipWaiting();
});

async function addToCache(key, value) {
  const cache = await caches.open(VERSION);
  await cache.put(key, value);
}

async function respondFromCache({ request, preloadResponse }) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    console.info(`[${request.url}] Response loaded from cache`);
    return cachedResponse;
  }

  const preloadResponsePromise = await preloadResponse;
  if (preloadResponse) {
    console.info(`[${request.url}] Response preloaded`);
    addToCache(request, preloadResponsePromise.clone());
    return preloadResponse;
  }

  try {
    const response = await fetch(request);
    addToCache(request, response.clone());
    return response;
  } catch (error) {
    console.error(`[Network error] ${error}`);
    return new Response("Network error", {
      status: 400,
      header: { "Content-Type": "text/plain" },
    });
  }
}
self.addEventListener("fetch", (event) => {
  event.respondWith(respondFromCache(event));
});
