/**
 * Contour density plot web component.
 *
 * Useful for displaying a two-dimensional distribution, such as those found in
 * vector variables like wind.
 */
export default class ChartDensity extends HTMLElement {
  static #TEMPLATE = `<p>Coming soon!</p>`;
  static #STYLE = ``;

  constructor() {
    super();

    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = ChartDensity.#STYLE + ChartDensity.#TEMPLATE;
  }
}
