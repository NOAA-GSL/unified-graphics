import { expect } from "@open-wc/testing";

import api from "../../src/unified_graphics/static/js/lib/api.js";

describe("api helpers", () => {
  describe("getJson", () => {
    it("returns a JavaScript object", async () => {
      const result = await api.getJson("/api/data/");
      expect(result).to.deep.equal([1, 2, 3]);
    });

    it("throws on HTTP errors");
  });
});
