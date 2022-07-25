import { extent, max, min } from "d3-array";

export default class ScalarVariableDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <ug-diag-scalarloop id=guess>
    <h3 slot=title>Observation &minus; Guess</h3>
  </ug-diag-scalarloop>
  <ug-diag-scalarloop id=analysis>
    <h3 slot=title>Observation &minus; Analysis</h3>
  </ug-diag-scalarloop>`;

  static #STYLE = `<style>
  * { margin: 0; }

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
