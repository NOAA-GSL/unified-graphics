import { expect, fixture } from "@open-wc/testing";

import ChartCartesian from "../../src/unified_graphics/static/js/component/ChartCartesian.js";
import "../../src/unified_graphics/static/js/component/ChartHistogram.js";

describe("ChartHistogram", () => {
  it("is a ChartCartesian", async () => {
    const el = await fixture("<chart-histogram></chart-histogram>");
    expect(el).to.be.an.instanceof(ChartCartesian);
  });

  describe("variable property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-histogram></chart-histogram>");
    });

    it("reflects the variable property as an attribute", () => {
      el.variable = "properties.adjusted";
      expect(el).to.have.attr("variable").equals("properties.adjusted");
    });

    it("defaults to null", () => {
      expect(el.variable).to.be.null;
    });
  });

  describe("variable attribute", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(
        "<chart-histogram variable='properties.adjusted'></chart-histogram>"
      );
    });

    it("reflects the variable attribute as a property", () => {
      expect(el.variable).equals("properties.adjusted");
    });

    it("removes the variable attribute when the property is null", () => {
      el.variable = null;
      expect(el).not.to.have.attr("variable");
    });
  });

  describe("bins", () => {
    it("defaults to an empty array");
    it("works on an array of values");
    it("uses the variable path to read from an array of objects");
  });
});
