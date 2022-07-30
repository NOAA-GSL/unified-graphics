import { describe, expect, it } from "vitest";

import { zip } from "../../src/js/utils";

describe("zip", () => {
  it("combines two arrays", () => {
    const result = Array.from(zip([1, 2, 3], ["a", "b", "c"]));

    expect(result).toEqual([
      [1, "a"],
      [2, "b"],
      [3, "c"],
    ]);
  });

  it.each([
    [
      [1, 2],
      ["a", "b", "c"],
      [
        [1, "a"],
        [2, "b"],
      ],
    ],
    [
      [1, 2, 3],
      ["a", "b"],
      [
        [1, "a"],
        [2, "b"],
      ],
    ],
    [[], ["a", "b"], []],
    [[1, 2], [], []],
  ])("stops after reaching the end of the shortest array", (a, b, expected) => {
    const result = Array.from(zip(a, b));

    expect(result).toEqual(expected);
  });

  it("returns an empty array by default", () => {
    const result = Array.from(zip());

    expect(result).toEqual([]);
  });

  it("returns an empty array for an empty array", () => {
    const result = Array.from(zip([]));

    expect(result).toEqual([]);
  });

  it("nests items of a single array", () => {
    const result = Array.from(zip([1, 2, 3]));

    expect(result).toEqual([[1], [2], [3]]);
  });
});
