import {
  axisBottom,
  axisRight,
  bin,
  deviation,
  extent,
  format,
  max,
  mean,
  min,
  scaleLinear,
  select,
} from "../vendor/d3.js";

import Margin from "../lib/Margin.js";
import ChartCartesian from "./ChartCartesian.js";

/**
 * @typedef {Array.<number>} D3Bin
 * @property {number} x0 The lower bound of the bin
 * @property {number} x1 The upper bound of the bin
 */

/**
 * @typedef {D3Bin[]} D3BinArray
 * @see {@link https://github.com/d3/d3-array/blob/v3.2.0/README.md#bins}
 */

/**
 * Render a histogram for data.
 *
 * @property {number[]} data Values to visualize
 * @readonly
 * @property {D3BinArray} bins Binned `data` for the histogram.
 * @readonly
 * @property {number} deviation The standard deviation for `data`
 * @readonly
 * @property {number} mean The mean for `data`
 * @property thresholds {(number[]|function)}
 *   An array of numbers defining the bin boundaries or a function that
 *   generates those boundaries from `data`. There will be `thresholds.length`
 *   + 1 bins in the histogram.
 *   @see {@link https://github.com/d3/d3-array/blob/v3.2.0/README.md#bin_thresholds}
 * @property {string} variable - A JavaScript path for looking up the variable
 *   displayed as the distribution from the loaded data. Reflected as an attribute on
 *   the HTML element.
 *   @see {@link https://lodash.com/docs/4.17.15#get}
 */
export default class ChartHistogram extends ChartCartesian {
  get css() {
    return `:host {
    display: block;
    user-select: none;
  }

  .deviation rect,
  #selection {
    fill: #dfe1e2;
    mix-blend-mode: color-burn;
  }

  .annotation line {
    stroke: currentColor;
  }

  .annotation text {
    font-weight: bold;
    text-shadow: 1px 1px 1px white;
  }`;
  }

  /** @type {?number[]} **/
  #thresholds = null;

  /** @type {number | undefined} */
  #mean = 0;

  /** @type {number | undefined} */
  #deviation = 0;

  get bins() {
    const binner = bin();
    const data = this.data.length > 0 ? this.data[0].data : [];

    if (this.thresholds) {
      binner.thresholds(this.thresholds);
    } else {
      const scale = scaleLinear().domain(extent(data)).nice(160);
      binner.thresholds(scale.ticks(160));
    }

    return binner(data);
  }

  get thresholds() {
    return this.#thresholds;
  }

  set thresholds(value) {
    this.#thresholds = value;
    this.update();
  }

  get variable() {
    return this.getAttribute("variable");
  }

  set variable(value) {
    if (!value) {
      this.removeAttribute("variable");
    } else {
      this.setAttribute("variable", value);
    }
  }

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    if (!(width && height)) return;

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = new Margin(fontSize, 0, fontSize, 0);

    svg.attr("viewBox", `0 0 ${width} {height}`);

    const hasData = this.data.length > 0 && this.data[0].data.length > 0;
    if (!hasData) return;

    const data = this.bins;

    // Store the x scale so we can invert values from mouse events.
    const xScale = scaleLinear()
      .domain(
        this.thresholds
          ? extent(this.thresholds)
          : [min(data, (d) => d.x0), max(data, (d) => d.x1)]
      )
      .range([margin.left, width - margin.horizontal]);

    const maxCount = max(data, (series) => max(series.data, (bin) => bin.length));
    const yScale = scaleLinear()
      .domain([0, maxCount])
      .range([height - margin.vertical, margin.top]);

    const xAxis = axisBottom(xScale).tickFormat(format(this.formatX));
    const yAxis = axisRight(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(format(this.formatY))
      .tickSize(width);

    svg
      .select(".data")
      .attr("transform", `translate({margin.left}, ${margin.top})`)
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("fill", "#2378c3")
      .attr("x", (d) => xScale(d.x0))
      .attr("y", (d) => yScale(d.length))
      .attr("width", (d) => xScale(d.x1) - xScale(d.x0))
      .attr("height", (d) => yScale(0) - yScale(d.length));

    // Left-align the annotations if the mean of the distribution is to the
    // left of center in the chart, otherwise we'll right-align the text.
    const leftAligned = xScale(this.mean) <= width / 2;

    const annotation = svg
      .select(".annotation")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    annotation
      .selectAll(".deviation")
      .data([null])
      .join((enter) => enter.append("g").attr("class", "deviation"))
      .attr("transform", `translate(${xScale(this.mean - this.deviation)},1)`)
      .call((g) => {
        const fmt = xAxis.tickFormat();
        const y = fontSize * 3;
        const width =
          xScale(this.mean + this.deviation) - xScale(this.mean - this.deviation);
        let x1 = width;
        let x2 = width + 0.75 * fontSize;
        let x = width + fontSize;
        let anchor = "start";

        if (!leftAligned) {
          x1 = 0;
          x2 = -0.75 * fontSize;
          x = -fontSize;
          anchor = "end";
        }

        g.selectAll("rect")
          .data([null])
          .join("rect")
          .attr("width", width)
          .attr("height", height - margin.top - margin.bottom);

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("x1", x1)
          .attr("y1", y)
          .attr("x2", x2)
          .attr("y2", y);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("x", x)
          .attr("y", y)
          .attr("dominant-baseline", "middle")
          .attr("text-anchor", anchor)
          .text(`σ = ${fmt(this.deviation)}`);
      });

    annotation
      .selectAll(".mean")
      .data([null])
      .join((enter) => enter.append("g").attr("class", "mean"))
      .attr("transform", `translate(${xScale(this.mean)},0)`)
      .call((g) => {
        const fmt = xAxis.tickFormat();
        let x = fontSize * 0.25;
        let anchor = "start";

        if (!leftAligned) {
          x *= -1;
          anchor = "end";
        }

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("y2", height - margin.top - margin.bottom);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("dominant-baseline", "middle")
          .attr("x", x)
          .attr("y", fontSize * 1.5)
          .attr("text-anchor", anchor)
          .text(`mean = ${fmt(this.mean)}`);
      });

    annotation
      .selectAll(".count")
      .data([null])
      .join((enter) => enter.append("text").attr("class", "count"))
      .attr("text-anchor", "end")
      .attr("dominant-baseline", "top")
      .attr("x", width - margin.left - margin.right)
      .text(`Observations: ${yAxis.tickFormat()(this.data.length)}`);

    svg
      .select(".x-axis")
      .attr("transform", `translate(${margin.left}, ${height - margin.bottom})`)
      .call(xAxis);

    svg
      .select(".y-axis")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .call(yAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll(".tick text").attr("x", 4).attr("dy", -4);
      });
  }
}

customElements.define("chart-histogram", ChartHistogram);
