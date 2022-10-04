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

import ChartElement from "./ChartElement";
import { bin2d } from "./Chart.helpers";

export default class Chart2DHistogram extends ChartElement {
  static get observedAttributes() {
    return ChartElement.observedAttributes;
  }

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().parentElement.getBoundingClientRect();

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
    let domain = this.domain;
    let range = this.range;

    if (!domain) domain = extent(data, (d) => d.direction);
    if (!range) range = extent(data, (d) => d.magnitude);

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
