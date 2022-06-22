import { cleanup, render } from "@testing-library/svelte";
import { afterEach, describe, expect, test } from "vitest";

import VariableDiag from "$lib/components/VariableDiag";

describe("VariableDiag.svelte", () => {
  afterEach(() => cleanup());

  test.each([
    [{ title: "Temperature" }, "Temperature"],
    [{ title: "Moisture" }, "Moisture"],
  ])("displays the variable name", (props, expected) => {
    const { getByRole } = render(VariableDiag, props);

    expect(getByRole("heading").innerHTML).toEqual(expected);
  });
});
