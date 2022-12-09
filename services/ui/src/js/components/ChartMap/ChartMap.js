/** @module components/ChartMap */

import {
  extent,
  geoAlbers,
  geoPath,
  scaleQuantize,
  scaleSqrt,
  schemePuOr,
  schemePurples,
} from "d3";

import ChartElement from "../ChartElement";

/**
 * @typedef {[[number, number], [number, number]]} Region
 * A bounding box describing a region selected on the map. It consists of two
 * coordinates, the first defines the left, top corner of the region, the
 * second defines the right, bottom corner.
 */

/**
 * @event ChartMap#BrushEvent
 * @type {object}
 * @property {Region} detail The bounding box for the current selection
 */

/**
 * Return the value used as the radius for each datum.
 * @callback radiusAccessor
 * @param {object} datum The observation being plotted on the map
 * @return {number} The value that will be mapped to the bubble's radius for
 *   `datum`
 */

/**
 * A bubble map component.
 *
 * @property {object[]} data A GeoJSON object to be plotted on the map
 * @property {radiusAccessor} radius An accessor function to
 *   retrieve the radius value for each datum
 * @property {[number, number][]} selection A bounding box for the map
 *   selection consisting of two tuples, the first of which is the left, top
 *   corner, and the second of which is the right, bottom corner
 *   @readonly
 *   @property {object} scale - a d3.scaleQuantize object for the fill colors on the map
 * @fires ChartMap#BrushEvent
 */
export default class ChartMap extends ChartElement {
  static #TEMPLATE = `<canvas id="data"></canvas><canvas id="selection"></canvas>`;

  static #STYLE = `:host {
    contain: size layout style;

    display: grid;
    grid-template-areas: main;

    cursor: crosshair;
  }

  :host > * {
    grid-area: main;
  }`;

  #projection = geoAlbers();

  /** @type {?[number, number][]} */
  #selection = null;

  #borders = null;
  #data = null;

  /** @type radiusAccessor */
  #radiusAccessor = (d) => d;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = `<style>${ChartMap.#STYLE}</style>
      ${ChartMap.#TEMPLATE}`;
  }

  connectedCallback() {
    fetch("/geo/borders.json")
      .then((response) => response.json())
      .then((json) => {
        this.#borders = json;
        this.update();
      });

    const canvas = this.shadowRoot?.getElementById("selection");

    if (canvas) {
      canvas.addEventListener("mousedown", this.mousedownCallback);
    }
  }

  disconnectedCallback() {
    const canvas = this.shadowRoot?.getElementById("selection");

    if (canvas) {
      canvas.removeEventListener("mousedown", this.mousedownCallback);
    }
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#data = value;

    // FIXME: This is duplicated across all charts to ensure that they fire
    // this event. This event is used by the ColorRamp component so that it
    // knows when to update itself and could be useful for other chart
    // interactions.
    const event = new CustomEvent("chart-datachanged", { bubbles: true });
    this.dispatchEvent(event);

    this.update();
  }

  get radius() {
    return this.#radiusAccessor;
  }

  set radius(fn) {
    this.#radiusAccessor = fn;
  }

  get scale() {
    const observations = this.#data;

    if (!observations) return scaleQuantize().range(schemePurples[9]);

    /** @type number[] */
    const [lower, upper] = extent(observations.features, this.#radiusAccessor);

    const isDiverging = lower / Math.abs(lower) !== upper / Math.abs(upper);
    const largestBound = Math.max(Math.abs(lower), Math.abs(upper));

    return isDiverging
      ? scaleQuantize().domain([-largestBound, largestBound]).range(schemePuOr[9])
      : scaleQuantize().domain([lower, upper]).range(schemePurples[9]);
  }

  get selection() {
    return this.#selection;
  }

  set selection(value) {
    this.#selection = value;
    this.#brush();
  }

  render() {
    const canvas = this.shadowRoot?.getElementById("data");

    if (!canvas) return;

    const height = this.height;
    const width = this.width;

    if (height === undefined || width === undefined) return;

    for (let c of this.shadowRoot.querySelectorAll("canvas")) {
      c.setAttribute("width", width.toString());
      c.setAttribute("height", height.toString());
    }

    const borders = this.#borders;
    const observations = this.#data;

    if (!(borders || observations)) return;

    this.#projection.fitSize([width, height], observations ?? borders);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const path = geoPath(this.#projection, ctx);

    if (borders) {
      ctx.save();
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = "#000";

      ctx.beginPath();
      path(borders);
      ctx.stroke();

      ctx.restore();
    }

    if (!(observations && this.#radiusAccessor)) return;

    const fill = this.scale;

    /** @type number[] */
    const [lower, upper] = extent(observations.features, this.#radiusAccessor);

    const r = scaleSqrt()
      .domain([0, Math.max(Math.abs(lower), Math.abs(upper))])
      .range([0.5, 6]);

    observations.features.forEach((feature) => {
      const value = this.#radiusAccessor(feature);
      const radius = r(Math.abs(value));
      const [x, y] = this.#projection(feature.geometry.coordinates);

      ctx.save();
      ctx.fillStyle = fill(value);

      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fill();

      ctx.restore();
    });

    this.#brush();
  }

  mousedownCallback = ({ target, offsetX, offsetY }) => {
    const [lng, lat] = this.#projection.invert([offsetX, offsetY]);

    this.#selection = [
      [lng, lat],
      [lng, lat],
    ];

    target.addEventListener("mousemove", this.mousemoveCallback);
    window.addEventListener("mouseup", this.mouseupCallback, { once: true });
  };

  mousemoveCallback = ({ offsetX, offsetY }) => {
    this.#selection[1] = this.#projection.invert([offsetX, offsetY]);
    this.#brush();
  };

  mouseupCallback = () => {
    this.shadowRoot
      ?.getElementById("selection")
      ?.removeEventListener("mousemove", this.mousemoveCallback);

    const [[x0, y0], [x1, y1]] = this.#selection;

    if (x0 === x1 || y0 === y1) {
      this.#selection = null;
      this.#brush();
    }

    let left, right, top, bottom;

    if (x0 < x1) {
      left = x0;
      right = x1;
    } else {
      left = x1;
      right = x0;
    }

    if (y0 > y1) {
      top = y0;
      bottom = y1;
    } else {
      top = y1;
      bottom = y0;
    }

    const brush = new CustomEvent("chart-brush", {
      bubbles: true,
      detail:
        this.#selection === null
          ? null
          : [
              [left, top],
              [right, bottom],
            ],
    });
    this.dispatchEvent(brush);
  };

  #brush() {
    const canvas = this.shadowRoot?.getElementById("selection");
    const ctx = canvas.getContext("2d");
    const path = geoPath(this.#projection, ctx);

    ctx.clearRect(0, 0, this.width, this.height);

    if (!this.#selection) return;

    const [[x0, y0], [x1, y1]] = this.#selection;
    let left, right, top, bottom;

    if (x0 < x1) {
      left = x0;
      right = x1;
    } else {
      left = x1;
      right = x0;
    }

    if (y0 > y1) {
      top = y0;
      bottom = y1;
    } else {
      top = y1;
      bottom = y0;
    }
    const polygon = {
      type: "Feature",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [left, top],
            [right, top],
            [right, bottom],
            [left, bottom],
            [left, top],
          ],
        ],
      },
    };

    ctx.save();
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = "#aaa";

    ctx.beginPath();
    path(polygon);
    ctx.fill();
    ctx.restore();
  }
}
