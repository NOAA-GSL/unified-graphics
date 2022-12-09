/** @module components/ColorRamp */

import { format, select } from "d3";

/**
 * Generate lower and upper bounds for a set of scale thresholds
 *
 * @param scale {object} - A d3.scaleThreshold or d3.scaleQuantize object
 * @return Array.<[number, number]>
 */
function thresholdBoundaries(scale) {
  const thresholds = [null, ...scale.thresholds(), null];
  let boundaries = [];

  for (let i = 0, n = thresholds.length - 1; i < n; i++) {
    boundaries.push([thresholds[i], thresholds[i + 1]]);
  }

  return boundaries;
}

/**
 * Render a color ramp.
 *
 * Color ramps are used as legends when a variable is encoded using color to
 * indicate the scale of different color values. It can be continuous or
 * discrete.
 *
 * @property for {string} - The ID of a chart with a scale property for which this color ramp will display a legend.
 * @property format {string} - A format string for D3's formatter that is used to format the threshold labels
 */
export default class ColorRamp extends HTMLElement {
  static #TEMPLATE = `<slot></slot>
    <svg viewBox="0 0 300 16"></svg>`;

  static #STYLE = `:host {
    contain: content;
    display: block;
    font: inherit;
  }

  rect {
    stroke: white;
  }

  text {
    dominant-baseline: hanging;
    text-anchor: middle;
    font: inherit;
  }`;

  /**
   * The request ID from requestAnimationFrame when an update is pending.
   * @type {?number}
   */
  #pendingUpdate = null;

  static get observedAttributes() {
    return ["for", "format"];
  }

  constructor() {
    super();

    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${ColorRamp.#STYLE}</style>${ColorRamp.#TEMPLATE}`;
  }

  connectedCallback() {
    document.addEventListener("chart-datachanged", this.onDataChanged);
  }

  disconnectedCallback() {
    document.removeEventListener("chart-datachanged", this.onDataChanged);
  }

  get for() {
    return this.getAttribute("for");
  }

  set for(value) {
    if (!value) {
      this.removeAttribute("for");
    } else {
      this.setAttribute("for", value);
    }

    this.update();
  }

  get format() {
    return this.getAttribute("format") ?? ",d";
  }

  set format(value) {
    if (!value) {
      this.removeAttribute("format");
    } else {
      this.setAttribute("format", value);
    }

    this.update();
  }

  /**
   * Re-render when the data changes on the chart this legend is for.
   */
  onDataChanged = (event) => {
    if (event.target.id !== this.for) return;
    this.update();
  };

  /**
   * Schedule an update to the component
   */
  update() {
    if (this.#pendingUpdate) return;

    this.#pendingUpdate = window.requestAnimationFrame(() => {
      this.#pendingUpdate = null;
      this.render();
    });
  }

  render() {
    const chart = document.getElementById(this.for);

    if (!chart) return;

    const scale = chart.scale;

    if (!scale) return;

    const svg = select(this.shadowRoot).select("svg");
    const { width } = this.getBoundingClientRect();
    const fontSize = parseInt(getComputedStyle(this).fontSize);
    const height = fontSize * 1.75;
    const data = thresholdBoundaries(scale);
    const step = width / data.length;
    const fmt = format(this.format);

    svg
      .attr("viewBox", `0 0 ${width} ${height}`)
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("fill", (d) => scale(d[0] ?? d[1] - 1))
      .attr("x", (d, i) => i * step)
      .attr("y", fontSize)
      .attr("width", step)
      .attr("height", height - fontSize);

    svg
      .selectAll("text")
      .data(scale.thresholds())
      .join("text")
      .attr("transform", (d, i) => `translate(${(i + 1) * step}, 0)`)
      .text((d) => fmt(d));
  }
}
