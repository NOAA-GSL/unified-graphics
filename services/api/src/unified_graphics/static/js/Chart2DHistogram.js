/** @module components/Chart2DHistogram */

import ChartElement from "./ChartElement.js";
import { bin2d } from "./helpers.js";

/**
 * @typedef {object} DiagVector
 * @property {number} u
 * @property {number} v
 */

/**
 * Render a heatmap for data.
 *
 * @readonly
 * @property {object} bins Binned data for the histogram
 * @readonly
 * @property {number} contentHeight The height of the chart area excluding margins
 * @readonly
 * @property {number} contentWidth The width of the chart area excluding margins
 * @property {DiagVector[]} data Values to visualize
 * @readonly
 * @property {[number, number]} domain The min and max values for the x-axis
 * @property {string} formatX
 *   A d3 format string used to format values along the x-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-x`.
 * @property {string} formatY
 *   A d3 format string used to format values along the y-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-y`.
 * @readonly
 * @property {object} margin
 * @property {number} margin.top Top margin
 * @property {number} margin.right Right margin
 * @property {number} margin.bottom Bottom margin
 * @property {number} margin.left Left margin
 * @readonly
 * @property {[number, number]} range The min and max values for the y-axis
 * @readonly
 * @property {object} scale The color scale used for the bin counts
 * @property {string} src The URL for fetching GeoJSON data for the chart
 * @readonly
 * @property {object} xScale The scale used for the x-axis
 * @readonly
 * @property {object} yScale The scale used for the y-axis
 */
export default class Chart2DHistogram extends ChartElement {
  static #TEMPLATE = `<svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
    <rect id="selection"></rect>
  </svg>`;

  static #STYLE = `:host {
    display: block;
    user-select: none;
  }

  #selection {
    fill: #dfe1e2;
    mix-blend-mode: multiply;
  }`;

  /** @type {DiagVector[]} */
  #data = [];

  #selection = null;

  #xScale = d3.scaleLinear();
  #yScale = d3.scaleLinear();

  static get observedAttributes() {
    return ["format-x", "format-y", "src"].concat(
      ChartElement.observedAttributes
    );
  }

  constructor() {
    super();

    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${Chart2DHistogram.#STYLE}</style>
      ${Chart2DHistogram.#TEMPLATE}`;
  }

  connectedCallback() {
    const svg = this.shadowRoot.querySelector("svg");

    if (!svg) return;

    svg.addEventListener("mousedown", this.onMouseDown);
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
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

  get bins() {
    const binner = bin2d(
      this.xScale.ticks(Math.floor(this.contentWidth / 10)),
      this.yScale.ticks(Math.floor(this.contentHeight / 10))
    )
      .x((d) => d.u)
      .y((d) => d.v);

    return binner(this.#data);
  }

  get contentHeight() {
    const { top, bottom } = this.margin;
    return this.height - top - bottom;
  }

  get contentWidth() {
    const { left, right } = this.margin;
    return this.width - left - right;
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    if (Array.isArray(value)) {
      this.#data = value;
    } else {
      this.#data = value.features.map((d) => d.properties.adjusted);
    }

    // FIXME: This is duplicated across all charts to ensure that they fire
    // this event. This event is used by the ColorRamp component so that it
    // knows when to update itself and could be useful for other chart
    // interactions.
    const event = new CustomEvent("chart-datachanged", { bubbles: true });
    this.dispatchEvent(event);

    this.update();
  }

  // FIXME: These should be something we can set as properties / attributes
  // so that we can create multiple charts with the same axes.
  get domain() {
    if (!this.#data) return [0, 0];
    return d3.extent(this.#data, (d) => d.u);
  }

  get formatX() {
    return this.getAttribute("format-x") ?? ",";
  }

  set formatX(formatStr) {
    if (!formatStr) {
      this.removeAttribute("format-x");
    } else {
      this.setAttribute("format-x", formatStr);
    }
  }

  get formatY() {
    return this.getAttribute("format-y") ?? ",";
  }

  set formatY(formatStr) {
    if (!formatStr) {
      this.removeAttribute("format-y");
    } else {
      this.setAttribute("format-y", formatStr);
    }
  }

  // FIXME: These should be something we can set as properties / attributes
  // so that we can create multiple charts with the same axes.
  get range() {
    if (!this.#data) return [0, 0];
    return d3.extent(this.#data, (d) => d.v);
  }

  get margin() {
    const fontSize = parseInt(getComputedStyle(this).fontSize);

    return {
      top: fontSize,
      right: fontSize,
      bottom: fontSize,
      left: fontSize * 3,
    };
  }

  get scale() {
    return d3.scaleQuantize(
      d3.extent(this.bins, (d) => d.length),
      d3.schemeYlGnBu[9]
    );
  }

  get selection() {
    return structuredClone(this.#selection);
  }

  set selection(value) {
    this.#selection = structuredClone(value);
    this.#brush();
  }

  get src() {
    return this.getAttribute("src");
  }

  set src(value) {
    if (!value) {
      this.removeAttribute("src");
      return;
    }

    this.setAttribute("src", value);
  }

  get xScale() {
    return d3
      .scaleLinear()
      .domain(this.domain)
      .range([0, this.contentWidth])
      .nice();
  }

  get yScale() {
    return d3
      .scaleLinear()
      .domain(this.range)
      .range([this.contentHeight, 0])
      .nice();
  }

  onMouseDown = ({ currentTarget, offsetX, offsetY }) => {
    const { left, top } = this.margin;
    const x = this.#xScale.invert(offsetX - left);
    const y = this.#yScale.invert(offsetY - top);

    this.#selection = [
      [x, y],
      [x, y],
    ];

    window.addEventListener("mouseup", this.onMouseUp, { once: true });
    currentTarget.addEventListener("mousemove", this.onMouseMove);
  };

  onMouseMove = ({ offsetX, offsetY }) => {
    const { left, top } = this.margin;

    this.#selection[1] = [
      this.#xScale.invert(offsetX - left),
      this.#yScale.invert(offsetY - top),
    ];

    this.#brush();
  };

  onMouseUp = () => {
    this.shadowRoot
      .querySelector("svg")
      .removeEventListener("mousemove", this.onMouseMove);

    this.#brush();

    const brush = new CustomEvent("chart-brush", {
      bubbles: true,
      detail: this.selection,
    });
    this.dispatchEvent(brush);
  };

  render() {
    const svg = d3.select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    if (width === undefined || height === undefined) return;

    const fontSize = parseInt(getComputedStyle(this).fontSize);

    const contentWidth = this.contentWidth;
    const contentHeight = this.contentHeight;
    const margin = this.margin;

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    if (!this.#data?.length) return;

    const bins = this.bins;

    const fill = this.scale;
    const xScale = this.xScale;
    const yScale = this.yScale;

    const xAxis = d3
      .axisBottom(xScale)
      .tickFormat(d3.format(this.formatX))
      .tickSize(contentHeight);

    const yAxis = d3
      .axisLeft(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(d3.format(this.formatY))
      .tickSize(contentWidth);

    svg
      .select(".data")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .attr("stroke", "#a9aeb1")
      .attr("stroke-opacity", 0.6)
      .selectAll("rect")
      .data(bins)
      .join("rect")
      .attr("fill", (d) => fill(d.length))
      .attr("x", (d) => xScale(d.x0))
      .attr("y", (d) => yScale(d.y0))
      .attr("width", (d) => Math.abs(xScale(d.x1) - xScale(d.x0)))
      .attr("height", (d) => Math.abs(yScale(d.y1) - yScale(d.y0)));

    svg
      .select(".x-axis")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .call(xAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll("line").attr("stroke", "#dfe1e2");
      });

    svg
      .select(".y-axis")
      .attr(
        "transform",
        `translate(${margin.left + contentWidth}, ${margin.top})`
      )
      .call(yAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll("line").attr("stroke", "#dfe1e2");
      });

    svg
      .select("#selection")
      .attr("transform", `translate(${margin.left}, ${margin.right})`);
    this.#brush();
  }

  #brush() {
    if (this.#selection === null) return;

    const [x0, y0, x1, y1] = this.#selection
      .flat()
      .map((val, idx) =>
        idx % 2 === 0 ? this.#xScale(val) : this.#yScale(val)
      );

    d3.select(this.shadowRoot.querySelector("svg"))
      .select("#selection")
      .attr("x", Math.min(x0, x1))
      .attr("y", Math.min(y0, y1))
      .attr("width", Math.abs(x1 - x0))
      .attr("height", Math.abs(y1 - y0));
  }
}

customElements.define("chart-2dhistogram", Chart2DHistogram);
