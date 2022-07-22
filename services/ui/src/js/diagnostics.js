import { format } from "d3";

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
    this.shadowRoot.querySelector("#guess").data = data.guess;
    this.shadowRoot.querySelector("#analysis").data = data.analysis;
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
    </dl>`;

  static #STYLE = `<style>
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
    const { observations, mean, std } = data;

    this.shadowRoot.querySelector("#obs").textContent = this.formatCount(observations);
    this.shadowRoot.querySelector("#mean").textContent = this.formatStat(mean);
    this.shadowRoot.querySelector("#std").textContent = this.formatStat(std);
  }
}
