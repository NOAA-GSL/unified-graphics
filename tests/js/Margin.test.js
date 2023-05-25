import { expect } from "@open-wc/testing";

import Margin from "../../src/unified_graphics/static/js/lib/Margin.js";

describe("Margin", () => {
  it("defaults to 0 margins", () => {
    const m = new Margin();
    expect(m).to.deep.equal({ top: 0, right: 0, bottom: 0, left: 0 });
  });

  it("applies a single value to all margins", () => {
    const m = new Margin(1);
    expect(m).to.deep.equal({ top: 1, right: 1, bottom: 1, left: 1 });
  });

  it("applies two values to the vertical and horizontal margins", () => {
    const m = new Margin(1, 2);
    expect(m).to.deep.equal({ top: 1, right: 2, bottom: 1, left: 2 });
  });

  it("applies three values to the top, horizontal, and bottom margins", () => {
    const m = new Margin(1, 2, 3);
    expect(m).to.deep.equal({ top: 1, right: 2, bottom: 3, left: 2 });
  });

  it("applies four values to the top, right, bottom, and left margins", () => {
    const m = new Margin(1, 2, 3, 4);
    expect(m).to.deep.equal({ top: 1, right: 2, bottom: 3, left: 4 });
  });

  it("calculates the total horizontal margin", () => {
    const m = new Margin(1, 2, 3, 4);
    expect(m.horizontal).to.equal(6);
  });

  it("calculates the total vertical margin", () => {
    const m = new Margin(1, 2, 3, 4);
    expect(m.vertical).to.equal(4);
  });
});
