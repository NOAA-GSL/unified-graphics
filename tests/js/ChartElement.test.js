import { expect, defineCE, fixture } from "@open-wc/testing";
import { spy } from "sinon";
import Series from "../../src/unified_graphics/static/js/lib/Series.js";
import ChartElement from "../../src/unified_graphics/static/js/component/ChartElement";

const subject = defineCE(ChartElement);

/**
 * Mock ChartSource element for testing
 */
customElements.define(
  "chart-source",
  class extends HTMLElement {
    get data() {
      return new Series(this.getAttribute("name"), [1, 2, 3]);
    }
  }
);

describe("ChartElement", () => {
  describe("width property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject}></${subject}>`);
    });

    it("defaults to undefined", () => {
      expect(el.width).to.be.undefined;
    });

    it("is reflected as an attribute", () => {
      el.width = 100;
      expect(el.getAttribute("width")).to.equal("100");
    });
  });

  describe("height property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject}></${subject}>`);
    });

    it("defaults to undefined", () => {
      expect(el.height).to.be.undefined;
    });

    it("is reflected as an attribute", async () => {
      el.height = 100;
      expect(el.getAttribute("height")).to.equal("100");
    });
  });

  describe("width attribute", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject} width="100"></${subject}>`);
    });

    it("is converted to a number by the property", () => {
      expect(el.width).to.equal(100);
    });

    it("is removed when the property is set to null", () => {
      el.width = null;

      expect(el.hasAttribute("width")).to.be.false;
    });
  });

  describe("height attribute", () => {
    let el;

    beforeEach(async () => {
      el = await fixture(`<${subject} height="100"></${subject}>`);
    });

    it("is converted to a number by the property", () => {
      expect(el.height).to.equal(100);
    });

    it("is removed when the property is set to null", () => {
      el.height = null;

      expect(el.hasAttribute("height")).to.be.false;
    });
  });

  describe("render()", () => {
    let el, renderSpy;

    before(() => {
      renderSpy = spy(ChartElement.prototype, "render");
    });

    beforeEach(async () => {
      el = await fixture(`<${subject}></${subject}>`);
    });

    afterEach(() => {
      renderSpy.resetHistory();
    });

    after(() => {
      renderSpy.restore();
    });

    it("is called when the width property is set", () => {
      el.width = 100;
      expect(renderSpy.calledOnce).to.be.true;
    });

    it("is called when the width attribute is set", () => {
      el.setAttribute("width", "100");
      expect(renderSpy.calledOnce).to.be.true;
    });

    it("is called when the height property is set", () => {
      el.height = 100;
      expect(renderSpy.calledOnce).to.be.true;
    });

    it("is called when the height attribute is set", () => {
      el.setAttribute("height", "100");
      expect(renderSpy.calledOnce).to.be.true;
    });

    it("is only called once when width and height are set", () => {
      el.width = 100;
      el.height = 100;
      expect(renderSpy.calledOnce).to.be.true;
    });
  });

  describe("initialization", () => {
    let renderSpy;

    before(() => {
      renderSpy = spy(ChartElement.prototype, "render");
    });

    beforeEach(() => {
      renderSpy.resetHistory();
    });

    after(() => {
      renderSpy.restore();
    });

    it("calls render without width and height", async () => {
      await fixture(`<${subject}></${subject}>`);
      expect(renderSpy.calledOnce).to.be.true;
    });

    it("calls render when width and height are set", async () => {
      await fixture(`<${subject} width="100" height="100"></${subject}>`);
      expect(renderSpy.calledOnce).to.be.true;
    });
  });

  describe("data property", () => {
    it("is an empty array when there is no data", async () => {
      let el = await fixture(`<${subject}></${subject}>`);
      expect(el.data).to.be.deep.equal([]);
    });

    it("is a two-dimensional array", async () => {
      let el = await fixture(`<${subject}><chart-source></chart-source></${subject}>`);
      expect(el.data).to.be.deep.equal([{ data: [1, 2, 3] }]);
    });

    it("includes series names when available", async () => {
      let el = await fixture(`<${subject}>
          <chart-source name="first"></chart-source>
          <chart-source name="second"></chart-source>
        </${subject}>`);

      expect(el.data).to.be.deep.equal([
        { name: "first", data: [1, 2, 3] },
        { name: "second", data: [1, 2, 3] },
      ]);
    });
  });
});
