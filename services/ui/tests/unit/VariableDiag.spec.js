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

    expect(getByRole("heading", { level: 2 }).innerHTML).toEqual(expected);
  });

  test("displays OMB and OMA", () => {
    const { getAllByText, getByText } = render(VariableDiag);

    expect(() => getByText("Observation - Background")).not.toThrowError();
    expect(() => getByText("Observation - Analysis")).not.toThrowError();
    expect(getAllByText("Observations:")).toHaveLength(2);
  });
});
