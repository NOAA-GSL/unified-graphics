export class ScalarVariableDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <ug-diag-scalarloop id=guess>
    <h3 slot=title>Observation &minus; Guess</h3>
  </ug-diag-scalarloop>
  <ug-diag-scalarloop id=analysis>
    <h3 slot=title>Observation &minus; Analysis</h3>
  </ug-diag-scalarloop>`;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarVariableDiag.#TEMPLATE;
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
    }
  </style>`;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarLoopDiag.#STYLE + ScalarLoopDiag.#TEMPLATE;
  }

  set data(data) {
    this.update(data);
  }

  update(data) {
    const { observations, mean, std } = data;

    this.shadowRoot.querySelector("#obs").textContent = observations;
    this.shadowRoot.querySelector("#mean").textContent = mean;
    this.shadowRoot.querySelector("#std").textContent = std;
  }
}
