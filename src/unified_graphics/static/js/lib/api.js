/**
 * Fetch JSON data from a URL
 *
 * @param {string} url - The URL from which data is fetched
 */
function getJson(url) { }

// We’re exporting a default object instead of exporting individual functions so that we
// can stub these functions in our tests. Sinon can’t stub individual function exported
// from an ES module. We could look into using the import map plugin from Modern Web to
// mock the ES module with an import map.
// https://modern-web.dev/docs/test-runner/writing-tests/mocking/#using-import-maps-to-tests
export default {
  getJson,
};
