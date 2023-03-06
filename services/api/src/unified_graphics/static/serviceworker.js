const VERSION = "20230228"; // eslint-disable-line no-unused-vars

const APP_CACHE = `app-${VERSION}`;
const DATA_CACHE = `data-${VERSION}`;

// Track active fetch requests to avoid duplicate network requests.
const activeFetches = new Map();

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

/**
 * Return `true` if `request` is for an app resource, not data.
 *
 * Any request for JSON is considered a data request. Everything else is an app resource.
 */
function isAppResource(response) {
  const contentType = response.headers.get("Content-Type");
  return contentType !== "application/json";
}

/**
 * Add a response to the appropriate cache.
 */
async function addToCache(request, response) {
  const cacheName = isAppResource(response) ? APP_CACHE : DATA_CACHE;
  const cache = await caches.open(cacheName);
  console.info(`[addToCache] ${cacheName}`);
  await cache.put(request, response);
  if (activeFetches.has(request.url)) {
    console.info(`[addToCache] Removing fetch for ${request.url}`);
    activeFetches.delete(request.url);
  }
}

/**
 * Fetch data from the network
 *
 * Checks our currently open fetch requests to see if this one is a duplicate.
 * If so, use the response from the existing request, otherwise start a new one.
 */
async function networkResponse(request) {
  try {
    let response;

    // If we already have a fetch request for this URL, we'll use that response
    // instead of starting a new one.
    if (activeFetches.has(request.url)) {
      console.info(`[respondFromCache] Fetch in progress for ${request.url}`);
      response = await activeFetches.get(request.url);
    } else {
      console.info(`[respondFromCache] Starting fetch for ${request.url}`);
      activeFetches.set(request.url, fetch(request));
      response = await activeFetches.get(request.url);
      addToCache(request, response.clone());
    }
    return response.clone();
  } catch (error) {
    console.error(`[respondFromCache] Network error: ${error}`);
    return new Response("Network error", {
      status: 400,
      header: { "Content-Type": "text/plain" },
    });
  }
}

/**
 * Return a response for a fetch request prioritizing the cache over the network.
 */
async function respondFromCache(event) {
  const request = event.request;

  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    console.info(`[respondFromCache] Response loaded from cache: ${request.url}`);

    // If this is a cached response for the App (HTML, CSS, JS), return the
    // cached version and update the cache in the background so on the next
    // request there's an up-to-date response.
    if (isAppResource(cachedResponse)) {
      console.info(`[respondFromCache] Updating app cache`);
      const cache = await caches.open(APP_CACHE);
      event.waitUntil(cache.add(request));
    }

    return cachedResponse;
  }

  const preloadResponse = await event.preloadResponse;
  if (preloadResponse) {
    console.info(`[${request.url}] Response preloaded`);
    addToCache(request, preloadResponse.clone());
    return preloadResponse;
  }

  return networkResponse(request);
}

self.addEventListener("fetch", (event) => {
  event.respondWith(respondFromCache(event));
});
