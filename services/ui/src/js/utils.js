export function* zip(...args) {
  if (args.length < 1) return [];

  const n = args.map((arr) => arr.length).reduce((a, b) => Math.min(a, b));

  for (let i = 0; i < n; i++) {
    yield args.map((arr) => arr[i]);
  }
}

export function subtract(a, b) {
  return a - b;
}
