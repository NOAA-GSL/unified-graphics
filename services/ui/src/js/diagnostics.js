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
}
