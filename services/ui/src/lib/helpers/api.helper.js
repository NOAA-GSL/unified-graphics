// The string `__DIAG_API_HOST__` gets replaced by Vite with the value of
// process.env.UG_DIAG_API_HOST so that we can change where the API is expected
// to be
const DIAG_API_HOST = "__DIAG_API_HOST__";

export function diagnostics() {
  return fetch(`${DIAG_API_HOST}/diag/temperature`).then((response) => response.json());
}

export default {
  diagnostics,
};
