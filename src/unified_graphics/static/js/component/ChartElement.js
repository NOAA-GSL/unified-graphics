/**
 * Bass class for web component visualizations.
 *
 * `ChartElement` provides `width` and `height` properties for the
 * visualization that are reflected as observed attributes on the element for
 * ease of use. Setting these properties triggers a re-render of the
 * visualization. Renders are batched into a single frame with
 * `requestAnimationFrame` to prevent too many redraws when properties are
 * being set.
 *
 * @property {number} height The height of the element
 * @property {number} width The width of the element
 * @property {object[]} data - An array of data series
 */
class ChartElement extends HTMLElement {
  /**
   * The request ID from requestAnimationFrame when an update is pending.
   * @type {?number}
   */
  #pendingUpdate = null;

  static get observedAttributes() {
    return ["width", "height"];
  }

  connectedCallback() {
    this.addEventListener("chart-source-load", this.update.bind(this));
  }

  attributeChangedCallback(name) {
    switch (name) {
      case "height":
      case "width":
        this.update();
        break;
      default:
        break;
    }
  }

  get data() {
    let series = [];

    for (let src of this.querySelectorAll("chart-source")) {
      if (!src.data) continue;
      series.push(src.data);
    }

    return series;
  }

  get height() {
    const v = this.getAttribute("height");

    if (v) return +v;

    return undefined;
  }

  set height(value) {
    if (!value) {
      this.removeAttribute("height");
    } else {
      this.setAttribute("height", value.toString());
    }
  }

  get width() {
    const v = this.getAttribute("width");

    if (v) return +v;

    return undefined;
  }

  set width(value) {
    if (!value) {
      this.removeAttribute("width");
    } else {
      this.setAttribute("width", value.toString());
    }
  }

  /**
   * Schedule a call to the render method on the next frame.
   */
  update() {
    if (this.#pendingUpdate) return;

    this.#pendingUpdate = window.requestAnimationFrame(() => {
      this.#pendingUpdate = null;
      this.render();
    });
  }

  /**
   * Abstract method for rendering the visualization.
   */
  render() {}
}

export default ChartElement;
