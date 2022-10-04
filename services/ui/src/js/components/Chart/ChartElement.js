class ChartElement extends HTMLElement {
  static #TEMPLATE = `<span id="title-y"></span>
  <div class="container">
    <svg>
      <g class="x-axis"></g>
      <g class="y-axis"></g>
      <g class="data"></g>
      <g class="annotation"></g>
    </svg>
  </div>
  <span id="title-x"></span>`;

  static #STYLE = `:host {
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

    .container {
      position: relative;
      overflow: hidden;
      place-self: stretch;
    }

    .container > * {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
    }

    line,
    path,
    rect {
      shape-rendering: crispEdges;
    }`;

  #data = [];
  #range = null;
  #pendingUpdate = null;

  static get observedAttributes() {
    return ["format-x", "format-y", "src", "title-x", "title-y"];
  }

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = `<style>${this.componentStyles}</style>${
      ChartElement.#TEMPLATE
    }`;
  }

  connectedCallback() {
    this.resizeObserver = new ResizeObserver(() => {
      this.requestUpdate();
    });
    this.resizeObserver.observe(this.shadowRoot?.querySelector(".container"));
  }

  disconnectedCallback() {
    this?.resizeObserver.unobserve(this.shadowRoot?.querySelector(".container"));
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
        this.requestUpdate();
        break;
      case "title-x":
      case "title-y":
        this.#updateLabel(name, newValue);
        break;
      default:
        break;
    }
  }

  get componentStyles() {
    return ChartElement.#STYLE;
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#data = value;
    this.requestUpdate();
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
    return structuredClone(this.#range);
  }

  set range(value) {
    this.#range = value;
    this.requestUpdate();
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

  requestUpdate() {
    if (this.#pendingUpdate) return;

    this.#pendingUpdate = window.requestAnimationFrame(() => {
      this.#pendingUpdate = null;
      this.render();
    });
  }

  render() {}

  #updateLabel(id, value) {
    const span = this.shadowRoot?.getElementById(id);
    if (!span) return;
    span.textContent = value;
  }
}

export default ChartElement;
