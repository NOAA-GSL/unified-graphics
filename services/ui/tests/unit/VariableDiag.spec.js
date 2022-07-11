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
    const { getAllByText, getByText } = render(VariableDiag, {
      title: "Temperature",
      guess: {
        observations: 100,
        mean: 1.3,
        std: 0.1,
        bins: [],
      },
      analysis: {
        observations: 2000,
        mean: -1.2,
        std: 0.0004,
        bins: [],
      },
    });

    expect(() => getByText("Observation - Background")).not.toThrowError();
    expect(() => getByText("Observation - Analysis")).not.toThrowError();

    expect(getAllByText("Observations:")).toHaveLength(2);
    expect(getAllByText("Mean:")).toHaveLength(2);
    expect(getAllByText("Std. Dev.:")).toHaveLength(2);

    // Guess (OMB) statistics
    expect(() => getByText("100")).not.toThrowError();
    expect(() => getByText("1.300")).not.toThrowError();
    expect(() => getByText("0.100")).not.toThrowError();

    // Analysis (OMA) statistics
    expect(() => getByText("2,000")).not.toThrowError();
    expect(() => getByText("−1.200")).not.toThrowError();
    expect(() => getByText("0.000")).not.toThrowError();
  });
});
