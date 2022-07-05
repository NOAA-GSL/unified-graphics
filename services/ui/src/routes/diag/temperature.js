import debug from "debug";

import env from "$lib/helpers/env.helpers";

const logger = debug("unified-graphics:route");

export async function get() {
  logger("GET /diag/temperature/");

  const endpoint = `${env.diagApiHost}/diag/temperature/`;

  logger("Fetching %s", endpoint);

  const response = await fetch(endpoint);

  logger("Received: %s bytes", response.headers.get("content-length"));

  return response;
}
