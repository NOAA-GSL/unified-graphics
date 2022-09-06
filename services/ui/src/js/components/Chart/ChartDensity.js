import ChartElement from "./ChartElement";

/**
 * Contour density plot web component.
 *
 * Useful for displaying a two-dimensional distribution, such as those found in
 * vector variables like wind.
 */
export default class ChartDensity extends ChartElement {
  static #TEMPLATE = `<p>Coming soon!</p>`;
  static #STYLE = ``;

  static get observedAttributes() {
    return ChartElement.observedAttributes;
  }
}
