import { expect, fixture, oneEvent } from "@open-wc/testing";
import { promise, stub } from "sinon";

import api from "../../src/unified_graphics/static/js/lib/api.js";
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
      response.resolve("data goes here");
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.equal("data goes here");
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
      response.resolve("data goes here");
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.equal("data goes here");
    });
  });

  describe("data property", () => {
    let el;

    beforeEach(async () => {
      el = await fixture("<chart-source></chart-source>");
    });

    it("is undefined by default", () => {
      expect(el.data).to.be.undefined;
    });

    it("is frozen", async () => {
      el.src = "/api/data/";
      response.resolve([1, 2, 3]);
      await oneEvent(el, "chart-source-load");
      expect(el.data).to.be.frozen;
    });

    it("is read-only", () => {
      const setData = () => {
        el.data = "data";
      };
      expect(setData).to.throw(TypeError, /^Cannot set property data/);
    });
  });
});
