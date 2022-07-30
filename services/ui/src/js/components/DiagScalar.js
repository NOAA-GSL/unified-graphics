import { bin, extent, max, scaleLinear, select } from "d3";
import histogram from "../helpers/histogram.helper";

class DiagScalar extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
    <svg></svg>`;

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
  </style>`;

  #data = [];

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = DiagScalar.#STYLE + DiagScalar.#TEMPLATE;
  }

  static get observedAttributes() {
    return ["src"];
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

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "src") {
      fetch(newValue)
        .then((response) => response.json())
        .then((data) => {
          this.data = data;
        })
        .catch((err) => {
          console.error(err);
        });
    }
  }

  set data(data) {
    this.#data = data;
    this.update();
  }

  update() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = { bottom: fontSize };

    const x = scaleLinear().domain(extent(this.#data)).nice(160).range([0, width]);

    const binner = bin().thresholds(x.ticks(160));
    const data = binner(this.#data);

    const y = scaleLinear()
      .domain([0, max(data, (d) => d.length)])
      .range([height - margin.bottom, 0]);

    const chart = histogram().margin(margin).xScale(x).yScale(y).xFormat(" ,.3f");

    svg.attr("viewBox", `0 0 ${width} ${height}`).datum(data).call(chart);
  }
}

export default DiagScalar;
