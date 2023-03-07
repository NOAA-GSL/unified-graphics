import {
  axisBottom,
  axisRight,
  bin,
  deviation,
  extent,
  format,
  max,
  mean,
  min,
  scaleLinear,
  select,
} from "../vendor/d3.js";

import ChartElement from "./ChartElement.js";

/**
 * @typedef {Array.<number>} D3Bin
 * @property {number} x0 The lower bound of the bin
 * @property {number} x1 The upper bound of the bin
 */

/**
 * @typedef {D3Bin[]} D3BinArray
 * @see {@link https://github.com/d3/d3-array/blob/v3.2.0/README.md#bins}
 */

/**
 * Render a histogram for data.
 *
 * @property {number[]} data Values to visualize
 * @readonly
 * @property {D3BinArray} bins Binned `data` for the histogram.
 * @readonly
 * @property {number} deviation The standard deviation for `data`
 * @property {string} formatX
 *   A d3 format string used to format values along the x-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-x`.
 * @property {string} formatY
 *   A d3 format string used to format values along the y-axis. This property
 *   is reflected in an HTML attribute on the custom element called
 *   `format-y`.
 * @readonly
 * @property {number} mean The mean for `data`
 * @property thresholds {(number[]|function)}
 *   An array of numbers defining the bin boundaries or a function that
 *   generates those boundaries from `data`. There will be `thresholds.length`
 *   + 1 bins in the histogram.
 *   @see {@link https://github.com/d3/d3-array/blob/v3.2.0/README.md#bin_thresholds}
 */
export default class ChartHistogram extends ChartElement {
  static #TEMPLATE = `<svg>
    <g class="x-axis"></g>
    <g class="y-axis"></g>
    <g class="data"></g>
    <g class="annotation"></g>
    <rect id="selection"></rect>
  </svg>`;

  static #STYLE = `:host {
    display: block;
    user-select: none;
  }

  .deviation rect,
  #selection {
    fill: #dfe1e2;
    mix-blend-mode: color-burn;
  }

  .annotation line {
    stroke: currentColor;
  }

  .annotation text {
    font-weight: bold;
    text-shadow: 1px 1px 1px white;
  }`;

  /** @type {?number[]} **/
  #thresholds = null;

  /** @type {number[]} **/
  #data = [];

  /** @type {number | undefined} */
  #mean = 0;

  /** @type {number | undefined} */
  #deviation = 0;

  #selection = null;

  #xScale = scaleLinear();
  #yScale = scaleLinear();

  static get observedAttributes() {
    return ["format-x", "format-y", "src"].concat(ChartElement.observedAttributes);
  }

  constructor() {
    super();

    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${ChartHistogram.#STYLE}</style>
      ${ChartHistogram.#TEMPLATE}`;
  }

  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case "format-x":
      case "format-y":
        this.update();
        break;
      case "src":
        fetch(newValue)
          .then((response) => response.json())
          .then((data) => data.features.map((d) => d.properties.adjusted))
          .then((data) => (this.data = data));
        break;
      default:
        super.attributeChangedCallback(name, oldValue, newValue);
        break;
    }
  }

  connectedCallback() {
    const svg = this.shadowRoot.querySelector("svg");

    if (!svg) return;

    this.#selection = select(svg).select("#selection").datum([0, 0]);
    svg.addEventListener("mousedown", this.onMouseDown);
  }

  get bins() {
    const binner = bin();

    if (this.thresholds) {
      binner.thresholds(this.thresholds);
    } else {
      const scale = scaleLinear().domain(extent(this.data)).nice(160);
      binner.thresholds(scale.ticks(160));
    }

    return binner(this.data);
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#mean = mean(value);
    this.#deviation = deviation(value);

    this.#data = value;

    // FIXME: This is duplicated across all charts to ensure that they fire
    // this event. This event is used by the ColorRamp component so that it
    // knows when to update itself and could be useful for other chart
    // interactions.
    const event = new CustomEvent("chart-datachanged", { bubbles: true });
    this.dispatchEvent(event);

    this.update();
  }

  get deviation() {
    return this.#deviation;
  }

  get formatX() {
    return this.getAttribute("format-x") ?? ",";
  }

  set formatX(formatStr) {
    if (!formatStr) {
      this.removeAttribute("format-x");
    } else {
      this.setAttribute("format-x", formatStr);
    }
  }

  get formatY() {
    return this.getAttribute("format-y") ?? ",";
  }

  set formatY(formatStr) {
    if (!formatStr) {
      this.removeAttribute("format-y");
    } else {
      this.setAttribute("format-y", formatStr);
    }
  }

  get mean() {
    return this.#mean;
  }

  get selection() {
    return structuredClone(this.#selection.datum());
  }

  set selection(value) {
    this.#selection.datum(value).call(this.#brush);
  }

  get src() {
    return this.getAttribute("src");
  }

  set src(value) {
    if (!value) {
      this.removeAttribute("src");
      return;
    }

    this.setAttribute("src", value);
  }

  get thresholds() {
    return this.#thresholds;
  }

  set thresholds(value) {
    this.#thresholds = value;
    this.render();
  }

  /**
   * Handle mouse down events on the SVG.
   *
   * The mousedown event starts brushing on the histogram.
   *
   * **Note**: This has to be an arrow function assigned to a property so that
   * `this` refers to the ChartHistogram object. If it's defined as a regular
   * function, `this` will refer to the `<svg>` element that was clicked.
   *
   * @param {MouseEvent} event
   */
  onMouseDown = (event) => {
    const svg = event.currentTarget;
    // FIXME: Not sure I think persisting the selection in the DOM is wise
    // Pretty sure we stopped doing this for other charts.
    this.#selection.datum(
      [event.offsetX, event.offsetX].map((d) => this.#xScale.invert(d))
    );

    window.addEventListener("mouseup", this.onMouseUp, { once: true });
    svg.addEventListener("mousemove", this.onMouseMove);
  };

  /**
   * Update selection during mouse drags.
   *
   * **Note**: This has to be an arrow function assigned to a property so that
   * `this` refers to the ChartHistogram object. If it's defined as a regular
   * function, `this` will refer to the `<svg>` element that was clicked.
   *
   * @param {MouseEvent} event
   */
  onMouseMove = (event) => {
    this.#selection.datum()[1] = this.#xScale.invert(event.offsetX);
    this.#selection.call(this.#brush);
  };

  /**
   * Handle mouseup events on the SVG.
   *
   * This handler is connected by `onMouseDown` to register the end of the
   * brushing action.
   *
   * **Note**: This has to be an arrow function assigned to a property so that
   * `this` refers to the ChartHistogram object. If it's defined as a regular
   * function, `this` will refer to the `<svg>` element that was clicked.
   *
   * @param {MouseEvent} event
   */
  onMouseUp = () => {
    this.shadowRoot
      .querySelector("svg")
      .removeEventListener("mousemove", this.onMouseMove);

    // Set the selection to null if this.#selection.datum()the range is 0.
    let detail = structuredClone(this.#selection.datum());
    if (detail && detail[0] === detail[1]) {
      detail = null;
    }

    // Update the brush one last time because, in the event of a click with no
    // mousemove, this will never be called, leaving the old selection still
    // visible despite having updated the actual range.
    this.#selection.call(this.#brush);

    const brush = new CustomEvent("chart-brush", {
      bubbles: true,
      detail: detail,
    });
    this.dispatchEvent(brush);
  };

  render() {
    const svg = select(this.shadowRoot).select("svg");
    const height = this.height;
    const width = this.width;

    if (!(width && height)) return;

    const fontSize = parseInt(getComputedStyle(svg.node()).fontSize);
    const margin = { top: fontSize, right: 0, bottom: fontSize, left: 0 };

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    if (!this.data?.length) return;

    const data = this.bins;

    // Store the x scale so we can invert values from mouse events.
    const xScale = (this.#xScale = scaleLinear()
      .domain(
        this.thresholds
          ? extent(this.thresholds)
          : [min(data, (d) => d.x0), max(data, (d) => d.x1)]
      )
      .range([0, width - margin.left - margin.right]));

    const yScale = (this.#yScale = scaleLinear()
      .domain(this.range ?? [0, max(data, (d) => d.length)])
      .range([height - margin.top - margin.bottom, 0]));

    const xAxis = axisBottom(xScale).tickFormat(format(this.formatX));
    const yAxis = axisRight(yScale)
      .ticks(height / fontSize / 2)
      .tickFormat(format(this.formatY))
      .tickSize(width);

    svg
      .select(".data")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .selectAll("rect")
      .data(data)
      .join("rect")
      .attr("fill", "#2378c3")
      .attr("x", (d) => xScale(d.x0))
      .attr("y", (d) => yScale(d.length))
      .attr("width", (d) => xScale(d.x1) - xScale(d.x0))
      .attr("height", (d) => yScale(0) - yScale(d.length));

    // Left-align the annotations if the mean of the distribution is to the
    // left of center in the chart, otherwise we'll right-align the text.
    const leftAligned = xScale(this.mean) <= width / 2;

    const annotation = svg
      .select(".annotation")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    annotation
      .selectAll(".deviation")
      .data([null])
      .join((enter) => enter.append("g").attr("class", "deviation"))
      .attr("transform", `translate(${xScale(this.mean - this.deviation)},1)`)
      .call((g) => {
        const fmt = xAxis.tickFormat();
        const y = fontSize * 3;
        const width =
          xScale(this.mean + this.deviation) - xScale(this.mean - this.deviation);
        let x1 = width;
        let x2 = width + 0.75 * fontSize;
        let x = width + fontSize;
        let anchor = "start";

        if (!leftAligned) {
          x1 = 0;
          x2 = -0.75 * fontSize;
          x = -fontSize;
          anchor = "end";
        }

        g.selectAll("rect")
          .data([null])
          .join("rect")
          .attr("width", width)
          .attr("height", height - margin.top - margin.bottom);

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("x1", x1)
          .attr("y1", y)
          .attr("x2", x2)
          .attr("y2", y);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("x", x)
          .attr("y", y)
          .attr("dominant-baseline", "middle")
          .attr("text-anchor", anchor)
          .text(`σ = ${fmt(this.deviation)}`);
      });

    annotation
      .selectAll(".mean")
      .data([null])
      .join((enter) => enter.append("g").attr("class", "mean"))
      .attr("transform", `translate(${xScale(this.mean)},0)`)
      .call((g) => {
        const fmt = xAxis.tickFormat();
        let x = fontSize * 0.25;
        let anchor = "start";

        if (!leftAligned) {
          x *= -1;
          anchor = "end";
        }

        g.selectAll("line")
          .data([null])
          .join("line")
          .attr("y2", height - margin.top - margin.bottom);

        g.selectAll("text")
          .data([null])
          .join("text")
          .attr("dominant-baseline", "middle")
          .attr("x", x)
          .attr("y", fontSize * 1.5)
          .attr("text-anchor", anchor)
          .text(`mean = ${fmt(this.mean)}`);
      });

    annotation
      .selectAll(".count")
      .data([null])
      .join((enter) => enter.append("text").attr("class", "count"))
      .attr("text-anchor", "end")
      .attr("dominant-baseline", "top")
      .attr("x", width - margin.left - margin.right)
      .text(`Observations: ${yAxis.tickFormat()(this.data.length)}`);

    svg
      .select(".x-axis")
      .attr("transform", `translate(${margin.left}, ${height - margin.bottom})`)
      .call(xAxis);

    svg
      .select(".y-axis")
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .call(yAxis)
      .call((g) => {
        g.select(".domain").remove();
        g.selectAll(".tick text").attr("x", 4).attr("dy", -4);
      });

    this.#selection
      .attr("transform", `translate(${margin.left}, ${margin.top})`)
      .call(this.#brush);
  }

  /**
   * Update the brush selection
   *
   * @param {object} g - The D3 selection of the brush <rect>
   */
  #brush = (g) => {
    const y = Math.min(...this.#yScale.range());
    const height = Math.max(...this.#yScale.range()) - y;

    g.attr("x", (d) => this.#xScale(Math.min(...d)))
      .attr("y", y)
      .attr("width", (d) => Math.abs(this.#xScale(d[1]) - this.#xScale(d[0])))
      .attr("height", height);
  };
}

customElements.define("chart-histogram", ChartHistogram);
