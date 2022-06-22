import { cleanup, render } from "@testing-library/svelte";
import { afterEach, describe, it, expect } from "vitest";

import Header from "$lib/components/Header";

describe("Header.svelte", () => {
  afterEach(() => cleanup());

  it("has expected text", async () => {
    const result = render(Header);

    expect(result.getByRole("banner").innerHTML).toContain("Unified Graphics");
  });
});
