import {
  area,
  axisBottom,
  axisLeft,
  curveBumpX,
  extent,
  format,
  line,
  max,
  min,
  scaleLinear,
  scaleTime,
  select,
  timeFormat,
} from "../vendor/d3.js";

import ChartElement from "./ChartElement.js";

/**
 * Time series chart
 *
 * @property {string} current A UTC date string
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
    <g class="data">
      <path id="range"></path>
      <path id="mean"></path>
      <line id="current"></line>
    </g>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
  </svg>`;

  static #STYLE = `:host {
    display: block;
    user-select: none;
  }

  #range {
    fill: #aaa;
  }

  #current,
  #mean {
    fill: transparent;
    stroke: #000;
  }`;

  static get observedAttributes() {
    return ["current", "format-x", "format-y", "src"].concat(
      ChartElement.observedAttributes
    );
  }

  #data = [];
  #svg = null;

  constructor() {
    super();

    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${ChartTimeSeries.#STYLE}</style>
      ${ChartTimeSeries.#TEMPLATE}`;
    this.#svg = select(root.querySelector("svg"));
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "current":
        this.update();
        break;
      case "format-x":
      case "format-y":
        this.update();
        break;
      case "src":
        fetch(newValue)
          .then((response) => response.json())
          .then((data) => {
            // Convert dates from strings to Date objects.
            data.forEach((d) => {
              d.initialization_time = new Date(d.initialization_time);
            });
            return data;
          })
          .then((data) => (this.data = data));
        break;
      default:
        super.attributeChangedCallback(name, oldValue, newValue);
        break;
    }
  }

  get current() {
    return this.getAttribute("current");
  }
  set current(value) {
    if (!value) {
      this.removeAttribute("current");
    } else {
      this.setAttribute("current", value);
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
    return this.getAttribute("format-x") ?? "%Y-%m-%d";
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
    const domain = extent(this.#data, (d) => d.initialization_time);
    const { left, right } = this.margin;
    const width = this.width - left - right;
    return scaleTime().domain(domain).range([0, width]).nice();
  }

  get yScale() {
    const domain = [
      min(this.#data, (d) => d.obs_minus_forecast_adjusted.min),
      max(this.#data, (d) => d.obs_minus_forecast_adjusted.max),
    ];
    const { top, bottom } = this.margin;
    const height = this.height - top - bottom;

    return scaleLinear().domain(domain).range([height, 0]).nice();
  }

  render() {
    if (!(this.width && this.height)) return;

    const data = this.data;
    if (!data) return;

    const { xScale, yScale } = this;
    const rangeArea = area()
      .x((d) => xScale(d.initialization_time))
      .y0((d) => yScale(d.obs_minus_forecast_adjusted.min))
      .y1((d) => yScale(d.obs_minus_forecast_adjusted.max))
      .curve(curveBumpX);
    const meanLine = line()
      .x((d) => xScale(d.initialization_time))
      .y((d) => yScale(d.obs_minus_forecast_adjusted.mean))
      .curve(curveBumpX);

    this.#svg.attr("viewBox", `0 0 ${this.width} ${this.height}`);
    this.#svg
      .select(".data")
      .attr("transform", `translate(${this.margin.left}, ${this.margin.top})`);
    this.#svg.select("#range").datum(data).attr("d", rangeArea);
    this.#svg.select("#mean").datum(data).attr("d", meanLine);

    if (this.current) {
      this.#svg
        .select("#current")
        .datum(new Date(this.current))
        .attr("x1", xScale)
        .attr("x2", xScale)
        .attr("y1", yScale.range()[0])
        .attr("y2", yScale.range()[1]);
    }

    const xAxis = axisBottom(xScale).tickFormat(timeFormat(this.formatX));
    const yAxis = axisLeft(yScale).tickFormat(format(this.formatY));

    this.#svg
      .select(".x-axis")
      .attr(
        "transform",
        `translate(${this.margin.left}, ${this.height - this.margin.bottom})`
      )
      .call(xAxis);

    this.#svg
      .select(".y-axis")
      .attr("transform", `translate(${this.margin.left}, ${this.margin.top})`)
      .call(yAxis);
  }
}

customElements.define("chart-timeseries", ChartTimeSeries);
