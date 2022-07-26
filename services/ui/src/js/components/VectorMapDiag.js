export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <canvas></canvas>`;

  static #STYLE = `<style>
    :host {
      display: flex;
      flex-direction: column;
    }

    * {
      flex: 0 0 auto;
      margin: 0;
    }

    canvas {
      flex: 1 1 auto;
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
    this.resizeObserver.observe(this.shadowRoot?.querySelector("canvas"));
    this.update();
  }

  disconnectedCallback() {
    this.resizeObserver?.unobserve(this.shadowRoot?.querySelector("canvas"));
    delete this.resizeObserver;
  }

  update() {
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (!canvas) return;

    const { height, width } = canvas.getBoundingClientRect();

    canvas.setAttribute("width", width.toString());
    canvas.setAttribute("height", height.toString());
  }
}
