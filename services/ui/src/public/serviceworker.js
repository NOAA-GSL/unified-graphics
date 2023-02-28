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
