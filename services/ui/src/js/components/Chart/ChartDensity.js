import {
  axisBottom,
  axisRight,
  contourDensity,
  extent,
  format,
  geoPath,
  interpolateViridis,
  scaleLinear,
  scaleSequential,
  select,
} from "d3";

import ChartElement from "./ChartElement";

/**
 * Contour density plot web component.
 *
 * Useful for displaying a two-dimensional distribution, such as those found in
 * vector variables like wind.
 */
export default class ChartDensity extends ChartElement {
  static #STYLE = `.data path {
    shape-rendering: auto;
    stroke: #fff;
    stroke-opacity: 0.6;
  }`;

  #domain = null;

  static get observedAttributes() {
    return ChartElement.observedAttributes;
  }

  get componentStyles() {
    return super.componentStyles + ChartDensity.#STYLE;
  }

  get domain() {
    return structuredClone(this.#domain);
  }

  set domain(value) {
    this.#domain = structuredClone(value);
  }

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = { top: fontSize, right: 0, bottom: fontSize, left: 0 };

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    if (!this.data?.length) return;

    const data = this.data;
    let domain = this.domain;
    let range = this.range;

    if (!domain) domain = extent(data, (d) => d.direction);
    if (!range) range = extent(data, (d) => d.magnitude);

    const xScale = scaleLinear()
      .domain(domain)
      .range([0, width - margin.left - margin.right]);

    const yScale = scaleLinear()
      .domain(range)
      .range([height - margin.top - margin.bottom, 0]);

    const density = contourDensity()
      .x((d) => xScale(d.direction))
      .y((d) => yScale(d.magnitude))
      .size([width, height]);

    const contourData = density(data);

    const fill = scaleSequential(
      extent(contourData, (d) => d.value),
      interpolateViridis
    );

    const xAxis = axisBottom(xScale).tickFormat(format(this.formatX));
    const yAxis = axisRight(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(format(this.formatY))
      .tickSize(width);

    svg
      .select(".data")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .selectAll("path")
      .data(contourData)
      .join("path")
      .attr("fill", (d) => fill(d.value))
      .attr("d", geoPath());

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
