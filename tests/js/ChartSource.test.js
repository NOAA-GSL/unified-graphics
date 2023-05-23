import { expect, fixture, oneEvent } from "@open-wc/testing";
import { promise, stub } from "sinon";

import api from "../../src/unified_graphics/static/js/lib/api.js";
import Series from "../../src/unified_graphics/static/js/lib/Series.js";
import "../../src/unified_graphics/static/js/component/ChartSource.js";

describe("ChartSource", () => {
  let getJsonStub, response;

  beforeEach(() => {
    response = promise();
    getJsonStub = stub(api, "getJson");
    getJsonStub.withArgs("/api/data/").returns(response);
  });

  afterEach(() => {
    getJsonStub.restore();
  });

  describe("src attribute", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source src='/api/data/'></chart-source>");
    });

    it("fetches a URL", async () => {
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.deep.equal({ data: [1, 2, 3] });
    });

    it("is reflected by the src property", () => {
      expect(el.src).to.equal("/api/data/");
    });

    it("is removed by the src property", () => {
      el.src = null;
      expect(el.hasAttribute("src")).to.be.false;
    });
  });

  describe("src property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source></chart-source>");
    });

    it("is null by default", () => {
      expect(el.src).to.be.null;
    });

    it("reflects the property as an attribute", () => {
      el.src = "/api/data/";
      expect(el.getAttribute("src")).to.equal("/api/data/");
    });

    it("fetches a URL", async () => {
      el.src = "/api/data/";
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.deep.equal({ data: [1, 2, 3] });
    });
  });

  describe("data property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source></chart-source>");
    });

    it("is an empty Series by default", () => {
      expect(el.data).to.deep.equal({ data: [] });
    });

    it("is of type Series", async () => {
      el.src = "/api/data/";
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.be.an.instanceof(Series);
    });

    it("is read-only", () => {
      const setData = () => {
        el.data = "data";
      };
      expect(setData).to.throw(TypeError, /^Cannot set property data/);
    });
  });

  describe("name attribute", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source name='test' src='/api/data/'></chart-source>");
    });

    it("is reflected as a property", () => {
      expect(el.name).to.equal("test");
    });

    it("is removed when the name property is set to null", () => {
      el.name = null;
      expect(el.hasAttribute("name")).to.be.false;
    });

    it("is included in the Series object for the data", async () => {
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data.name).to.equal("test");
    });
  });

  describe("name property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source src='/api/data/'></chart-source>");
    });

    it("is reflected as an attribute", () => {
      el.name = "test";
      expect(el.getAttribute("name")).to.equal("test");
    });

    it("is included in the Series object for the data", async () => {
      el.name = "test";
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data.name).to.equal("test");
    });
  });

  describe("errors", () => {
    it("dispatches chart-source-error on HTTP errors");
  });
});
