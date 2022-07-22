import { extent, max, min } from "d3-array";
import { format } from "d3-format";
import { scaleLinear } from "d3-scale";
import * as d3 from "d3-selection";

export class ScalarVariableDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <ug-diag-scalarloop id=guess>
    <h3 slot=title>Observation &minus; Guess</h3>
  </ug-diag-scalarloop>
  <ug-diag-scalarloop id=analysis>
    <h3 slot=title>Observation &minus; Analysis</h3>
  </ug-diag-scalarloop>`;

  static #STYLE = `<style>
  :host {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  ::slotted([slot=title]) { grid-column: 1 / -1; }
  </style>`;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarVariableDiag.#STYLE + ScalarVariableDiag.#TEMPLATE;
  }

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "src") {
      fetch(newValue)
        .then((response) => response.json())
        .then((data) => this.update(data))
        .catch((reason) => {
          console.error(reason);
        });
    }
  }

  update(data) {
    const bins = data.guess.bins.concat(data.analysis.bins);

    const domain = [min(bins, (d) => d.lower), max(bins, (d) => d.upper)];
    const range = extent(bins, (d) => d.value);

    const guessEl = this.shadowRoot.querySelector("#guess");
    const anlEl = this.shadowRoot.querySelector("#analysis");

    guessEl.domain = anlEl.domain = domain;
    guessEl.range = anlEl.range = range;

    guessEl.data = data.guess;
    anlEl.data = data.analysis;
  }
}

export class ScalarLoopDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
    <dl>
      <dt>Observations</dt>
      <dd id=obs></dd>
      <dt>Mean</dt>
      <dd id=mean></dd>
      <dt>Std. Dev.</dt>
      <dd id=std></dd>
    </dl>
    <svg></svg>`;

  static #STYLE = `<style>
    :host {
      display: flex;
      flex-direction: column;
    }

    * { flex: 0 0 auto }
    svg {
      flex: 1 1 auto;
      align-self: stretch;
    }

    dl {
      display: grid;
      grid-template-columns: repeat(2, min-content);
      gap: 0.5rem;
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

  constructor() {
    super();

    this.formatCount = format(",");
    this.formatStat = format(" ,.3f");

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarLoopDiag.#STYLE + ScalarLoopDiag.#TEMPLATE;
  }

  set data(data) {
    this.update(data);
  }

  update(data) {
    const { bins, observations, mean, std } = data;

    this.shadowRoot.querySelector("#obs").textContent = this.formatCount(observations);
    this.shadowRoot.querySelector("#mean").textContent = this.formatStat(mean);
    this.shadowRoot.querySelector("#std").textContent = this.formatStat(std);

    const svg = d3.select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    const x = scaleLinear().domain(this.domain).range([0, width]);
    const y = scaleLinear().domain(this.range).range([height, 0]);

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    svg
      .selectAll("circle")
      .data(bins)
      .join("rect")
      .attr("x", (d) => x(d.lower))
      .attr("y", (d) => y(d.value))
      .attr("width", (d) => x(d.upper) - x(d.lower))
      .attr("height", (d) => y(0) - y(d.value));
  }
}
