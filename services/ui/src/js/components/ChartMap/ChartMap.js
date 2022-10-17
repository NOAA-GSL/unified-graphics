/** @module components/ChartMap */

import {
  extent,
  geoAlbers,
  geoPath,
  interpolatePuOr,
  interpolatePurples,
  scaleDiverging,
  scaleLinear,
  scaleSequential,
  scaleSqrt,
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
 * @fires ChartMap#BrushEvent
 */
export default class ChartMap extends ChartElement {
  static #TEMPLATE = `<canvas></canvas>`;

  static #STYLE = `host {
    cursor: crosshair;
  }`;

  #projection = geoAlbers();

  /** @type {?[number, number][]} */
  #selection = null;

  #mousedownWrapper = null;
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

    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      this.#mousedownWrapper = (event) => {
        this.mapMousedownCallback(event);
      };

      canvas.addEventListener("mousedown", this.#mousedownWrapper);
    }
  }

  disconnectedCallback() {
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      canvas.removeEventListener("mousedown", this.#mousedownWrapper);
      this.#mousedownWrapper = null;
    }
  }

  get data() {
    return structuredClone(this.#data);
  }

  set data(value) {
    this.#data = value;
    this.update();
  }

  get radius() {
    return this.#radiusAccessor;
  }

  set radius(fn) {
    this.#radiusAccessor = fn;
  }

  get selection() {
    return this.#selection;
  }

  set selection(value) {
    this.#selection = value;
    this.update();
  }

  render() {
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (!canvas) return;

    const height = this.height;
    const width = this.width;

    if (height === undefined || width === undefined) return;

    canvas.setAttribute("width", width.toString());
    canvas.setAttribute("height", height.toString());

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

    /** @type number[] */
    const [minDiff, maxDiff] = extent(observations.features, this.#radiusAccessor);

    const isDiverging = minDiff / Math.abs(minDiff) !== maxDiff / Math.abs(maxDiff);

    const fill = isDiverging
      ? scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff])
      : scaleSequential([minDiff, maxDiff], interpolatePurples);

    const r = scaleSqrt()
      .domain([0, Math.max(Math.abs(minDiff), Math.abs(maxDiff))])
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

    if (this.#selection) {
      const [[left, top], [right, bottom]] = this.#selection;
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

    // Legend
    const start = fill.domain()[0],
      stop = fill.domain()[fill.domain().length - 1],
      step = (stop - start) / (width / 2 - 16);

    const legendX = scaleLinear()
      .domain([start, stop])
      .range([16, width / 2]);

    ctx.save();

    for (let diff = start; diff <= stop; diff += step) {
      ctx.fillStyle = fill(diff);
      ctx.fillRect(legendX(diff), height - 32, 1, 32);
    }

    ctx.fillStyle = "black";
    ctx.textAlign = "center";
    fill.ticks().forEach((tick) => {
      ctx.fillRect(legendX(tick), height - 40, 1, 8);
      ctx.fillText(tick.toString(), legendX(tick), height - 48);
    });

    ctx.textAlign = "left";
    ctx.fillText("Speed (Observation − Forecast)", 16, height - 64);

    ctx.restore();
  }

  mapMousedownCallback({ target, offsetX, offsetY }) {
    const [lng, lat] = this.#projection.invert([offsetX, offsetY]);

    this.#selection = [
      [lng, lat],
      [lng, lat],
    ];

    const mouseupCallback = () => {
      window.removeEventListener("mouseup", mouseupCallback);
      target.removeEventListener("mousemove", mousemoveCallback);
      if (
        this.#selection[0][0] === this.#selection[1][0] &&
        this.#selection[0][1] === this.#selection[1][1]
      ) {
        this.#selection = null;
        this.update();
      }

      const brush = new CustomEvent("chart-brush", {
        bubbles: true,
        detail: this.#selection,
      });
      this.dispatchEvent(brush);
    };

    const mousemoveCallback = ({ offsetX, offsetY }) => {
      this.#selection[1] = this.#projection.invert([offsetX, offsetY]);
      this.update();
    };

    target.addEventListener("mousemove", mousemoveCallback);
    window.addEventListener("mouseup", mouseupCallback);
  }
}
