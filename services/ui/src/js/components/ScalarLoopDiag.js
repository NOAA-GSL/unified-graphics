import { axisBottom, axisRight } from "d3-axis";
import { format } from "d3-format";
import { scaleLinear } from "d3-scale";
import * as d3 from "d3-selection";

export default class ScalarLoopDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
    <dl>
      <dt>Observations</dt>
      <dd id=obs></dd>
      <dt>Mean</dt>
      <dd id=mean></dd>
      <dt>Std. Dev.</dt>
      <dd id=std></dd>
    </dl>
    <svg>
      <g class="data"></g>
      <g class="x-axis"></g>
      <g class="y-axis"></g>
    </svg>`;

  static #STYLE = `<style>
    :host {
      display: flex;
      flex-direction: column;
    }

    :host > * + * {
      margin-block-start: 0.5rem;
    }

    * {
      flex: 0 0 auto;
      margin: 0;
    }

    svg {
      flex: 1 1 auto;
      align-self: stretch;
      aspect-ratio: 4 / 3;
    }

    dl {
      display: grid;
      grid-template-columns: repeat(2, min-content);
      gap: 0 0.5rem;
    }

    dt {
      font-weight: bold;
      justify-self: end;
    }

    dt::after {
      content: ":";
    }

    dd {
      margin: 0;
      white-space: pre;
    }
  </style>`;

  domain = [0, 1];
  range = [0, 1];

  #data = {};

  constructor() {
    super();

    this.formatCount = format(",");
    this.formatStat = format(" ,.3f");

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarLoopDiag.#STYLE + ScalarLoopDiag.#TEMPLATE;
  }

  connectedCallback() {
    this.resizeObserver = new ResizeObserver(() => {
      this.update();
    });
    this.resizeObserver.observe(this.shadowRoot?.querySelector("svg"));
  }

  disconnectedCallback() {
    this?.resizeObserver.unobserve(this.shadowRoot?.querySelector("svg"));
    delete this?.resizeObserver;
  }

  set data(data) {
    this.#data = data;
    this.update();
  }

  update() {
    const { bins, observations, mean, std } = this.#data;

    this.shadowRoot.querySelector("#obs").textContent = this.formatCount(observations);
    this.shadowRoot.querySelector("#mean").textContent = this.formatStat(mean);
    this.shadowRoot.querySelector("#std").textContent = this.formatStat(std);

    const svg = d3.select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = fontSize;

    const x = scaleLinear()
      .domain(this.domain)
      .range([margin, width - 2 * margin]);
    const y = scaleLinear()
      .domain(this.range)
      .range([height - 2 * margin, margin]);

    const xAxis = axisBottom(x).tickFormat(this.formatStat);
    const yAxis = axisRight(y)
      .ticks(height / fontSize / 2)
      .tickFormat(this.formatCount)
      .tickSize(width - 2 * margin);

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    svg
      .select(".data")
      .selectAll("rect")
      .data(bins)
      .join("rect")
      .attr("x", (d) => x(d.lower))
      .attr("y", (d) => y(d.value))
      .attr("width", (d) => x(d.upper) - x(d.lower))
      .attr("height", (d) => y(0) - y(d.value));

    svg
      .select(".x-axis")
      .attr("transform", `translate(0, ${height - 2 * margin})`)
      .call(xAxis);

    svg
      .select(".y-axis")
      .attr("transform", `translate(${margin}, 0)`)
      .call(yAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll(".tick text").attr("x", 4).attr("dy", -4);
      });
  }
}
