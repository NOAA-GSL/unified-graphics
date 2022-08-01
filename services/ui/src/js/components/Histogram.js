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
  static #TEMPLATE = `<svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
  </svg>`;
  static #STYLE = `<style>
  :host {
    display: block;
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
    return ["src"];
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
}

export default Histogram;
