/** @module components/Chart2DHistogram */

import {
  axisBottom,
  axisLeft,
  extent,
  format,
  scaleLinear,
  scaleQuantize,
  schemeYlGnBu,
  select,
} from "d3";

import ChartElement from "../ChartElement";
import { bin2d } from "../../helpers";

/**
 * @typedef {object} DiagVector
 * @property {number} direction
 *   A value between 0 and 360 representing the orientation of the vector.
 * @property {number} magnitude The length of the vector.
 */

/**
 * Render a heatmap for data.
 *
 * @property {DiagVector[]} data Values to visualize
 * @property {string} formatX
 *   A d3 format string used to format values along the x-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-x`.
 * @property {string} formatY
 *   A d3 format string used to format values along the y-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-y`.
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

  #margin = { top: 0, right: 0, bottom: 0, left: 0 };
  #xScale = scaleLinear();
  #yScale = scaleLinear();

  static get observedAttributes() {
    return ["format-x", "format-y"].concat(ChartElement.observedAttributes);
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

  get selection() {
    return structuredClone(this.#selection);
  }

  set selection(value) {
    this.#selection = structuredClone(value);
    this.#brush();
  }

  onMouseDown = ({ currentTarget, offsetX, offsetY }) => {
    const x = this.#xScale.invert(offsetX - this.#margin.left);
    const y = this.#yScale.invert(offsetY - this.#margin.top);

    this.#selection = [
      [x, y],
      [x, y],
    ];

    window.addEventListener("mouseup", this.onMouseUp, { once: true });
    currentTarget.addEventListener("mousemove", this.onMouseMove);
  };

  onMouseMove = ({ offsetX, offsetY }) => {
    this.#selection[1] = [
      this.#xScale.invert(offsetX - this.#margin.left),
      this.#yScale.invert(offsetY - this.#margin.top),
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
    const svg = select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    if (width === undefined || height === undefined) return;

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = (this.#margin = {
      top: fontSize,
      right: fontSize,
      bottom: fontSize,
      left: fontSize * 3,
    });

    const contentWidth = width - margin.left - margin.right;
    const contentHeight = height - margin.top - margin.bottom;

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    if (!this.data?.length) return;

    const data = this.data;

    // FIXME: These should be something we can set as properties / attributes
    // so that we can create multiple charts with the same axes.

    /** @type {[number, number]} */
    let domain = extent(data, (d) => d.direction);

    /** @type {[number, number]} */
    let range = extent(data, (d) => d.magnitude);

    const xScale = (this.#xScale = scaleLinear()
      .domain(domain)
      .range([0, contentWidth])
      .nice());

    const yScale = (this.#yScale = scaleLinear()
      .domain(range)
      .range([contentHeight, 0])
      .nice());

    const binner = bin2d(
      xScale.ticks(Math.floor(contentWidth / 10)),
      yScale.ticks(Math.floor(contentHeight / 10))
    )
      .x((d) => d.direction)
      .y((d) => d.magnitude);

    const bins = binner(data);

    const fill = scaleQuantize(
      extent(bins, (d) => d.length),
      schemeYlGnBu[9]
    );

    const xAxis = axisBottom(xScale)
      .tickFormat(format(this.formatX))
      .tickSize(contentHeight);

    const yAxis = axisLeft(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(format(this.formatY))
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
      .attr("transform", `translate(${margin.left + contentWidth}, ${margin.top})`)
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
      .map((val, idx) => (idx % 2 === 0 ? this.#xScale(val) : this.#yScale(val)));

    select(this.shadowRoot.querySelector("svg"))
      .select("#selection")
      .attr("x", Math.min(x0, x1))
      .attr("y", Math.min(y0, y1))
      .attr("width", Math.abs(x1 - x0))
      .attr("height", Math.abs(y1 - y0));
  }
}
