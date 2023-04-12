import { extent, max, min, scaleLinear, scaleTime } from "../vendor/d3.js";

import ChartElement from "./ChartElement.js";

/**
 * Time series chart
 *
 * @property {string} formatX
 *   A d3 format string used to format values along the x-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-x`.
 * @property {string} formatY
 *   A d3 format string used to format values along the y-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-y`.
 * @property {string} src
 *   A URL for JSON data used in the time series. This property is reflected
 *   in an HTML attribute called `src`
 * @property {number[]} data Values visualizaed by the time series.
 */
export default class ChartTimeSeries extends ChartElement {
  static #TEMPLATE = `<svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
  </svg>`;

  static #STYLE = `:host {
    display: block;
    user-select: none;
  }`;

  static get observedAttributes() {
    return ["format-x", "format-y", "src"].concat(ChartElement.observedAttributes);
  }

  #data = [];

  constructor() {
    super();

    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${ChartTimeSeries.#STYLE}</style>
      ${ChartTimeSeries.#TEMPLATE}`;
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "format-x":
      case "format-y":
        this.update();
        break;
      case "src":
        fetch(newValue)
          .then((response) => response.json())
          .then((data) => (this.data = data));
        break;
      default:
        super.attributeChangedCallback(name, oldValue, newValue);
        break;
    }
  }

  get data() {
    return structuredClone(this.#data);
  }
  set data(value) {
    this.#data = value;
    this.update();
  }

  get formatX() {
    return this.getAttribute("format-x") ?? ",";
  }
  set formatX(value) {
    if (!value) {
      this.removeAttribute("format-x");
    } else {
      this.setAttribute("format-x", value);
    }
  }

  get formatY() {
    return this.getAttribute("format-y") ?? ",";
  }
  set formatY(value) {
    if (!value) {
      this.removeAttribute("format-y");
    } else {
      this.setAttribute("format-y", value);
    }
  }

  // FIXME: This is copied from Chart2DHistogram
  // We should probably have a more uniform interface for all of our chart components.
  get margin() {
    const fontSize = parseInt(getComputedStyle(this).fontSize);

    return {
      top: fontSize,
      right: fontSize,
      bottom: fontSize,
      left: fontSize * 3,
    };
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

  get xScale() {
    const domain = extent(this.#data, (d) => new Date(d.initialization_time));
    const { left, right } = this.margin;
    const width = width - left - right;
    return scaleTime().domain(domain).range([0, width]);
  }

  get yScale() {
    const domain = [
      min(this.#data, (d) => d.obs_minus_forecast_adjusted.min),
      max(this.#data, (d) => d.obs_minus_forecast_adjusted.max),
    ];
    const { top, bottom } = this.margin;
    const height = height - top - bottom;

    return scaleLinear().domain(domain).range([height, 0]);
  }

  render() {
    if (!(this.width && this.height)) return;
  }
}

customElements.define("chart-timeseries", ChartTimeSeries);
