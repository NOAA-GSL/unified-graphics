export function diagnostics() {
  return fetch("/diag/temperature").then((response) => response.json());
}

export default {
  diagnostics,
};
