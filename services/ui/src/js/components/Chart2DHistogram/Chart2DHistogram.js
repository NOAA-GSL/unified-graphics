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
  </svg>`;

  static #STYLE = `:host {
    display: block;
  }`;

  /** @type {DiagVector[]} */
  #data = [];

  static get observedAttributes() {
    return ["format-x", "format-y"].concat(ChartElement.observedAttributes);
  }

  constructor() {
    super();

    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${Chart2DHistogram.#STYLE}</style>
      ${Chart2DHistogram.#TEMPLATE}`;
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#data = value;
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

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    if (width === undefined || height === undefined) return;

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = {
      top: fontSize,
      right: fontSize,
      bottom: fontSize,
      left: fontSize * 3,
    };

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

    const xScale = scaleLinear().domain(domain).range([0, contentWidth]).nice();

    const yScale = scaleLinear().domain(range).range([contentHeight, 0]).nice();

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
  }
}
