import ChartElement from "./ChartElement.js";

/**
 * Base class representing a chart in cartesian coordinates with x- and y-axes.
 *
 * The class provides a `template` property that creates an SVG with groups for both the
 * x- and y-axis, following the D3 margin convention.
 *
 * @readonly
 * @property {string} template - A string containing the SVG template used by the
 *   ChartElement constructor in the shadowDom
 * @property {string} xFormat - A D3 format string used to format labels along the
 *   x-axis (reflected as the x-format attribute in HTML)
 * @property {string} yFormat - A D3 format string used to format labels along the
 *   y-axis (reflected as the y-format attribute in HTML)
 */
export default class ChartCartesian extends ChartElement {
  get template() {
    return `<svg>
  <g class="x axis"></g>
  <g class="y axis"></g>
</svg>`;
  }

  get xFormat() {
    return this.hasAttribute("x-format") ? this.getAttribute("x-format") : ",";
  }

  set xFormat(value) {
    if (!value) {
      this.removeAttribute("x-format");
    } else {
      this.setAttribute("x-format", value);
    }
  }

  get yFormat() {
    return this.hasAttribute("y-format") ? this.getAttribute("y-format") : ",";
  }

  set yFormat(value) {
    if (!value) {
      this.removeAttribute("y-format");
    } else {
      this.setAttribute("y-format", value);
    }
  }
}
