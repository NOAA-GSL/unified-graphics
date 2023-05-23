import api from "../lib/api.js";
import Series from "../lib/Series.js";

/**
 * Data has been successfully loaded.
 *
 * @event chart-source-load
 * @type {Event}
 */
const CHART_SOURCE_LOAD = "chart-source-load";

/**
 * Data loading element for charts.
 *
 * A Web Component used to load JSON data from a URL.
 *
 * @example
 * <chart-histogram>
 *   <chart-source src="/api/data/"></chart-source>
 * </chart-histogram>
 *
 * @property {string} src - The URL from which data is fetched, also available as an
 *  attribute on the HTML element
 * @readonly
 * @property {Series} data - A copy of the data loaded from the URL
 *
 * @fires chart-source-load
 */
export default class ChartSource extends HTMLElement {
  #data = Object.freeze([]);

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "src":
        if (!newValue) {
          return;
        }

        api.getJson(newValue).then((data) => {
          this.#data = Object.freeze(data);
          this.dispatchEvent(new Event(CHART_SOURCE_LOAD));
        });
        break;
      default:
        super.attributeChangedCallback(name, oldValue, newValue);
        break;
    }
  }

  get data() {
    return new Series(this.name, this.#data);
  }

  get name() {
    return this.getAttribute("name");
  }

  set name(value) {
    if (!value) {
      this.removeAttribute("name");
    } else {
      this.setAttribute("name", value);
    }
  }

  get src() {
    return this.getAttribute("src");
  }

  set src(value) {
    if (!value) {
      this.removeAttribute("src");
    } else {
      this.setAttribute("src", value);
    }
  }
}

customElements.define("chart-source", ChartSource);
