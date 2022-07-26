import { select } from "d3-selection";

export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <svg></svg>`;

  static #STYLE = `<style>
    svg {
      aspect-ratio: 4 / 3;
    }
  </style>`;

  #data = {};

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = VectorMapDiag.#STYLE + VectorMapDiag.#TEMPLATE;
  }

  set data(data) {
    this.#data = data;
    this.update();
  }

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "src") {
      fetch(newValue)
        .then((response) => response.json())
        .then((data) => {
          this.data = data;
        })
        .catch((reason) => {
          console.error(reason);
        });
    }
  }

  connectedCallback() {
    this.resizeObserver = new ResizeObserver(() => {
      this.update();
    });
    this.resizeObserver.observe(this.shadowRoot?.querySelector("svg"));
    this.update();
  }

  disconnectedCallback() {
    this.resizeObserver?.unobserve(this.shadowRoot?.querySelector("svg"));
    delete this.resizeObserver;
  }

  update() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    svg.attr("viewBox", `0 0 ${width} ${height}`);
  }
}
