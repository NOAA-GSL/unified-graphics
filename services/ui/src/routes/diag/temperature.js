import env from "$lib/helpers/env.helpers";

export async function get() {
  const response = await fetch(`${env.diagApiHost}/diag/temperature/`);

  return response;
}
