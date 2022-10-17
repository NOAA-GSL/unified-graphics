/** @module utils */

/**
 * Combine multiple arrays into an array of tuples.
 *
 * @example
 * // returns [[1, "a"], [2, "b"], [3, "c"]]
 * Array.from(zip([1, 2, 3], ["a", "b", "c"]]))
 *
 * @param {...Array} args - One or more arrays to zip up
 * @yields {Array}
 */
export function* zip(...args) {
  if (args.length < 1) return [];

  const n = args.map((arr) => arr.length).reduce((a, b) => Math.min(a, b));

  for (let i = 0; i < n; i++) {
    yield args.map((arr) => arr[i]);
  }
}

/**
 * Subtract `b` from `a`.
 *
 * Useful for Array.prototype.reduce.
 *
 * @param {number} a
 * @param {number} b
 *
 * @returns {number}
 */
export function subtract(a, b) {
  return a - b;
}
