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
} from "d3";

import ChartElement from "../ChartElement";

class ChartHistogram extends ChartElement {
  static #TEMPLATE = `<svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
    <g class="annotation"></g>
  </svg>`;

  static #STYLE = `:host {
    display: block;
  }

  .deviation rect {
    fill: #dfe1e2;
    mix-blend-mode: color-burn;
  }

  .annotation line {
    stroke: currentColor;
  }`;

  #thresholds = null;
  #data = [];
  #mean = 0;
  #deviation = 0;

  static get observedAttributes() {
    return ["format-x", "format-y"].concat(ChartElement.observedAttributes);
  }

  constructor() {
    super();

    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${ChartHistogram.#STYLE}</style>
      ${ChartHistogram.#TEMPLATE}`;
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "format-x":
      case "format-y":
        this.update();
        break;
      default:
        super.attributeChangedCallback(name, oldValue, newValue);
        break;
    }
  }

  get bins() {
    const binner = bin();

    if (this.thresholds) {
      binner.thresholds(this.thresholds);
    } else {
      const scale = scaleLinear().domain(extent(this.data)).nice(160);
      binner.thresholds(scale.ticks(160));
    }

    return binner(this.data);
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#mean = mean(value);
    this.#deviation = deviation(value);

    this.#data = value;
  }

  get deviation() {
    return this.#deviation;
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

  get mean() {
    return this.#mean;
  }

  get thresholds() {
    return this.#thresholds;
  }

  set thresholds(value) {
    this.#thresholds = value;
    this.render();
  }

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = { top: fontSize, right: 0, bottom: fontSize, left: 0 };

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    if (!this.data?.length) return;

    const data = this.bins;

    const xScale = scaleLinear()
      .domain(
        this.thresholds
          ? extent(this.thresholds)
          : [min(data, (d) => d.x0), max(data, (d) => d.x1)]
      )
      .range([0, width - margin.left - margin.right]);

    const yScale = scaleLinear()
      .domain(this.range ?? [0, max(data, (d) => d.length)])
      .range([height - margin.top - margin.bottom, 0]);

    const xAxis = axisBottom(xScale).tickFormat(format(this.formatX));
    const yAxis = axisRight(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(format(this.formatY))
      .tickSize(width);

    svg
      .select(".data")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("fill", "#2378c3")
      .attr("x", (d) => xScale(d.x0))
      .attr("y", (d) => yScale(d.length))
      .attr("width", (d) => xScale(d.x1) - xScale(d.x0))
      .attr("height", (d) => yScale(0) - yScale(d.length));

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

        g.selectAll("rect")
          .data([null])
          .join("rect")
          .attr(
            "width",
            xScale(this.mean + this.deviation) - xScale(this.mean - this.deviation)
          )
          .attr("height", height - margin.top - margin.bottom);

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("x2", -0.75 * fontSize);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("x", -fontSize)
          .attr("text-anchor", "end")
          .attr("dominant-baseline", "middle")
          .text(`σ = ${fmt(this.deviation)}`);
      });

    annotation
      .selectAll(".mean")
      .data([null])
      .join((enter) => enter.append("g").attr("class", "mean"))
      .attr("transform", `translate(${xScale(this.mean)},0)`)
      .call((g) => {
        const fmt = xAxis.tickFormat();

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("y2", height - margin.top - margin.bottom);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("dominant-baseline", "middle")
          .attr("x", fontSize * 0.25)
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

export default ChartHistogram;
