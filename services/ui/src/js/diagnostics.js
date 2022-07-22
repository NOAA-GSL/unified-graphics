export class ScalarDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <dl>
    <dt>Observations</dt>
    <dd id=obs></dd>
    <dt>Mean</dt>
    <dd id=mean></dd>
    <dt>Std. Dev.</dt>
    <dd id=std></dd>
  </dl>`;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ScalarDiag.#TEMPLATE;
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
    const { observations, mean, std } = data.guess;

    this.shadowRoot.querySelector("#obs").textContent = observations;
    this.shadowRoot.querySelector("#mean").textContent = mean;
    this.shadowRoot.querySelector("#std").textContent = std;
  }
}
