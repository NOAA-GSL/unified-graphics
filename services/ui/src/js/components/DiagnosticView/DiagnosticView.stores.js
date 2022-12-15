import { writable } from "svelte/store";

export const region = writable(null);
export const range = writable(null);
export const filteredObservations = writable(new Set());
