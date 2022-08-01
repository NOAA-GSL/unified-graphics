import {
  axisBottom,
  axisRight,
  bin,
  extent,
  format,
  max,
  min,
  scaleLinear,
  select,
} from "d3";

class Histogram extends HTMLElement {
  static #TEMPLATE = `<span id="title-y"></span>
  <svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
  </svg>
  <span id="title-x"></span>`;

  static #STYLE = `<style>
  :host {
    display: grid;
    gap: 0.5em;
    grid-template-columns: min-content 1fr;
    grid-template-rows: 1fr min-content;
    place-items: center;
  }

  #title-x,
  svg {
    grid-column: 2 / 3;
  }

  #title-y,
  svg {
    grid-row: 1 / 2;
  }

  #title-y {
    writing-mode: vertical-lr;
    transform: rotate(180deg);
  }

  #title-x,
  .x-axis {
    color: #3d4551;
  }

  #title-y,
  .y-axis {
    color: #71767a;
  }

  svg {
    place-self: stretch;
    aspect-ratio: 4 / 3;
  }

  line,
  rect {
    shape-rendering: crispEdges;
  }
  </style>`;

  #data = [];
  #thresholds = null;
  #range = null;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = Histogram.#STYLE + Histogram.#TEMPLATE;
  }

  static get observedAttributes() {
    return ["format-x", "format-y", "src", "title-x", "title-y"];
  }

  connectedCallback() {
    this.resizeObserver = new ResizeObserver(() => {
      this.render();
    });
    this.resizeObserver.observe(this.shadowRoot?.querySelector("svg"));
  }

  disconnectedCallback() {
    this?.resizeObserver.unobserve(this.shadowRoot?.querySelector("svg"));
    delete this?.resizeObserver;
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "src":
        fetch(newValue)
          .then((response) => response.json())
          .then((data) => {
            this.data = data;
            this.dispatchEvent(new CustomEvent("data-load", { bubbles: true }));
          })
          .catch((err) => {
            console.error(err);
          });
        break;
      case "format-x":
      case "format-y":
        this.render();
        break;
      case "title-x":
      case "title-y":
        this.#updateLabel(name, newValue);
        break;
      default:
        break;
    }
  }

  get bins() {
    const binner = bin();

    if (this.thresholds) binner.thresholds(this.thresholds);

    return binner(this.data);
  }

  get data() {
    return this.#data;
  }

  set data(value) {
    this.#data = value;
    this.render();
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

  get range() {
    return this.#range;
  }

  set range(value) {
    this.#range = value;
    this.render();
  }

  get src() {
    return this.getAttribute("src");
  }

  set src(value) {
    if (!value) {
      this.removeAttribute("src");
      this.data = [];
    } else {
      this.setAttribute("src", value);
    }
  }

  get thresholds() {
    return this.#thresholds;
  }

  set thresholds(value) {
    this.#thresholds = value;
    this.render();
  }

  get titleX() {
    return this.getAttribute("title-x");
  }

  set titleX(value) {
    if (!value) {
      this.removeAttribute("title-x");
    } else {
      this.setAttribute("title-x", value);
    }
  }

  get titleY() {
    return this.getAttribute("title-y");
  }

  set titleY(value) {
    if (!value) {
      this.removeAttribute("title-y");
    } else {
      this.setAttribute("title-y", value);
    }
  }

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = { top: fontSize, right: 0, bottom: fontSize, left: 0 };

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

    svg.attr("viewBox", `0 0 ${width} ${height}`);

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

  #updateLabel(id, value) {
    const span = this.shadowRoot?.getElementById(id);
    if (!span) return;
    span.textContent = value;
  }
}

export default Histogram;