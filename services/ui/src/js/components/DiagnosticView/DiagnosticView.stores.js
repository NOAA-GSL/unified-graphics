import { writable } from "svelte/store";

export const region = writable([
  [0, 0],
  [0, 0],
]);
export const range = writable([0, 0]);
export const filteredObservations = writable(new Set());
