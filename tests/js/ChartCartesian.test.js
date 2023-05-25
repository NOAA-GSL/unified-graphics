import { defineCE, expect, fixture } from "@open-wc/testing";

import ChartElement from "../../src/unified_graphics/static/js/component/ChartElement.js";
import ChartCartesian from "../../src/unified_graphics/static/js/component/ChartCartesian.js";

const subject = defineCE(ChartCartesian);

describe("ChartCartesian", () => {
  it("is a ChartElement", async () => {
    const el = await fixture(`<${subject}></${subject}>`);
    expect(el).to.be.an.instanceof(ChartElement);
  });

  describe("template", () => {
    let el;

    before(async () => {
      el = await fixture(`<${subject}></${subject}>`);
    });

    it("has an svg", async () => {
      const svgCount = el.shadowRoot.querySelectorAll("svg").length;
      expect(svgCount).to.equal(1);
    });

    it("has an svg in the root", () => {
      expect(el.shadowRoot.querySelector("svg").parentNode).to.equal(el.shadowRoot);
    });

    it("has an x-axis", async () => {
      const xAxisCount = el.shadowRoot.querySelectorAll("svg > g.x.axis").length;
      expect(xAxisCount).to.equal(1);
    });

    it("has an y-axis", async () => {
      const yAxisCount = el.shadowRoot.querySelectorAll("svg > g.y.axis").length;
      expect(yAxisCount).to.equal(1);
    });
  });

  describe("axis format string properties", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject}></${subject}>`);
    });

    it("reflects the xFormat property to the x-format attribute", () => {
      el.xFormat = "s";
      expect(el.getAttribute("x-format")).to.equal("s");
    });

    it("has a default xFormat of ','", () => {
      expect(el.xFormat).to.equal(",");
    });

    it("reflects the yFormat property to the y-format attribute", () => {
      el.yFormat = "s";
      expect(el.getAttribute("y-format")).to.equal("s");
    });

    it("has a default yFormat of ','", () => {
      expect(el.yFormat).to.equal(",");
    });
  });

  describe("axis format string attributes", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject} x-format="s" y-format="s"></${subject}>`);
    });

    it("reflects the x-format attribute to the xFormat property", () => {
      expect(el.xFormat).to.equal("s");
    });

    it("removes the x-format attribute when xFormat is null", () => {
      el.xFormat = null;
      expect(el.hasAttribute("x-format")).to.be.false;
    });

    it("reflects the y-format attribute to the yFormat property", () => {
      expect(el.yFormat).to.equal("s");
    });

    it("removes the y-format attribute when yFormat is null", () => {
      el.yFormat = null;
      expect(el.hasAttribute("y-format")).to.be.false;
    });
  });

  it("uses the margin convention");
});
