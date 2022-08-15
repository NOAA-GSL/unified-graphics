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

export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <div class="grid">
    <canvas></canvas>
    <div>
      <chart-histogram id="wind-speed" title-x="Wind Speed (Observation − Forecast)" title-y="Observation Count" format-x=" ,.3f"></chart-histogram>
      <chart-histogram id="wind-direction" title-x="Wind Direction (Observation − Forecast)" title-y="Observation Count" format-x=" ,.3f"></chart-histogram>
    </div>
  </div>`;

  static #STYLE = `<style>
    :host {
      display: flex;
      flex-direction: column;
      gap: 1em;
    }

    * {
      flex: 0 0 auto;
      margin: 0;
    }

    canvas {
      aspect-ratio: 4 / 3;
      cursor: crosshair;
    }

    chart-histogram + chart-histogram {
      margin-block-start: 1em;
    }

    .grid{
      flex: 1 1 auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(640px, 100%), 1fr));
      grid-template-rows: min-content 1fr min-content;
      place-items: stretch;
      gap: 1em;
    }
  </style>`;

  #selection = null;
  #mousedownWrapper = null;
  #pendingUpdate = null;

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = VectorMapDiag.#STYLE + VectorMapDiag.#TEMPLATE;

    this.showVectors = shadowRoot.querySelector("[type=checkbox]");
  }

  connectedCallback() {
    this.addEventListener("data-changed", this.update);
    this.showVectors?.addEventListener("change", () => {
      this.update();
    });
    this.resizeObserver = new ResizeObserver(this.update);

    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      this.#mousedownWrapper = (event) => {
        this.mapMousedownCallback(event);
      };

      this.resizeObserver.observe(canvas);
      canvas.addEventListener("mousedown", this.#mousedownWrapper);
    }

    this.update();
  }

  disconnectedCallback() {
    this.removeEventListener("data-changed", this.update);

    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      this.resizeObserver?.unobserve(canvas);
      canvas.removeEventListener("mousedown", this.#mousedownWrapper);
      this.#mousedownWrapper = null;
    }

    delete this.resizeObserver;
  }

  requestUpdate() {
    if (this.#pendingUpdate) {
      window.cancelAnimationFrame(this.#pendingUpdate);
    }

    this.#pendingUpdate = window.requestAnimationFrame(() => {
      this.update();
    });
  }

  update() {
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (!canvas) return;

    const { height, width } = canvas.getBoundingClientRect();

    canvas.setAttribute("width", width.toString());
    canvas.setAttribute("height", height.toString());

    const borders = this.querySelector("#borders")?.data;
    const observations = this.querySelector("#observations")?.data;

    if (!(borders || observations)) return;

    const projection = geoAlbers().fitSize([width, height], observations ?? borders);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    if (borders) {
      const path = geoPath(projection, ctx);

      ctx.save();
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = "#000";

      ctx.beginPath();
      path(borders);
      ctx.stroke();

      ctx.restore();
    }

    if (!observations) return;

    const [minDiff, maxDiff] = extent(
      observations.features,
      (feature) => feature.properties.guess.magnitude
    );

    const isDiverging = minDiff / Math.abs(minDiff) !== maxDiff / Math.abs(maxDiff);

    const fill = isDiverging
      ? scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff])
      : scaleSequential([minDiff, maxDiff], interpolatePurples);

    const r = scaleSqrt()
      .domain([0, Math.max(Math.abs(minDiff), Math.abs(maxDiff))])
      .range([0.5, 6]);

    console.log(fill.domain());

    observations.features.forEach((feature) => {
      const radius = r(Math.abs(feature.properties.guess.magnitude));
      const [x, y] = projection(feature.geometry.coordinates);

      ctx.save();
      ctx.fillStyle = fill(feature.properties.guess.magnitude);

      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fill();

      ctx.restore();
    });

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
    this.#selection = [
      [offsetX, offsetY],
      [offsetX, offsetY],
    ];

    const mouseupCallback = () => {
      window.removeEventListener("mouseup", mouseupCallback);
      target.removeEventListener("mousemove", mousemoveCallback);
      if (
        this.#selection[0][0] === this.#selection[1][0] &&
        this.#selection[0][1] === this.#selection[1][1]
      ) {
        this.#selection = null;
        this.requestUpdate();
      }
    };

    const mousemoveCallback = ({ offsetX, offsetY }) => {
      this.#selection[1] = [offsetX, offsetY];
      this.requestUpdate();
    };

    target.addEventListener("mousemove", mousemoveCallback);
    window.addEventListener("mouseup", mouseupCallback);
  }
}
