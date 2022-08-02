import {
  extent,
  geoPath,
  geoTransform,
  interpolatePuOr,
  scaleDiverging,
  scaleLinear,
  scaleSqrt,
} from "d3";

export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <div class="grid">
    <canvas></canvas>
    <chart-histogram title-x="Wind Speed (Observation − Forecast)" title-y="Observation Count" format-x=" ,.3f"></chart-histogram>
  </div>
  <label>
    <input type="checkbox">
    Show vector direction
  </label>`;

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

  #data = {};

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
      this.resizeObserver.observe(canvas);
    }

    this.update();
  }

  disconnectedCallback() {
    this.removeEventListener("data-changed", this.update);

    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      this.resizeObserver?.unobserve(canvas);
    }

    delete this.resizeObserver;
  }

  update() {
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (!canvas) return;

    const { height, width } = canvas.getBoundingClientRect();

    canvas.setAttribute("width", width.toString());
    canvas.setAttribute("height", height.toString());

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const obs = this.querySelector("#observation")?.data;
    const fcst = this.querySelector("#forecast")?.data;

    if (!obs && !fcst) return;

    const coords = [].concat(obs?.coords ?? [], fcst?.coords ?? []);

    const x = scaleLinear()
      .domain(extent(coords, (d) => d[0] - 360))
      .range([0, width]);
    const y = scaleLinear()
      .domain(extent(coords, (d) => d[1]))
      .range([height, 0]);

    if (obs && fcst) {
      const obsMinusFcst = obs.magnitude.map((magObs, idx) => [
        ...obs.coords[idx],
        magObs - fcst.magnitude[idx],
      ]);
      const [minDiff, maxDiff] = extent(obsMinusFcst, (d) => d[2]);
      const fill = scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff]);
      const r = scaleSqrt()
        .domain([0, Math.max(Math.abs(minDiff), Math.abs(maxDiff))])
        .range([0.5, 6]);

      obsMinusFcst.forEach((omf) => {
        const [lng, lat, delta] = omf;

        ctx.beginPath();
        ctx.arc(x(lng - 360), y(lat), r(Math.abs(delta)), 0, 2 * Math.PI);

        ctx.fillStyle = fill(delta);
        ctx.fill();
      });

      const hist = this.shadowRoot?.querySelector("chart-histogram");
      if (hist) {
        hist.data = obsMinusFcst.map((d) => d[2]);
      }
    }

    if (obs && this.showVectors?.checked) {
      ctx.beginPath();

      obs.direction.forEach((heading, idx) => {
        const [lng, lat] = obs.coords[idx];
        const heading_r = ((heading + 90) * Math.PI) / 180;
        // FIXME: This constant length should be configurable
        const dx = 6 * Math.cos(heading_r);
        const dy = 6 * Math.sin(heading_r);

        ctx.moveTo(x(lng - 360), y(lat));
        ctx.lineTo(x(lng - 360) + dx, y(lat) + dy);
      });

      ctx.stroke();
    }

    if (fcst && this.showVectors?.checked) {
      ctx.beginPath();

      fcst.direction.forEach((heading, idx) => {
        const [lng, lat] = fcst.coords[idx];
        const heading_r = ((heading + 90) * Math.PI) / 180;
        // FIXME: This constant length should be configurable
        const dx = 6 * Math.cos(heading_r);
        const dy = 6 * Math.sin(heading_r);

        ctx.moveTo(x(lng - 360), y(lat));
        ctx.lineTo(x(lng - 360) + dx, y(lat) + dy);
      });

      ctx.strokeStyle = "#888888";
      ctx.stroke();
    }

    const border = this.querySelector("#border")?.data;
    if (border) {
      const path = geoPath(
        geoTransform({
          point: function (lng, lat) {
            this.stream.point(x(lng), y(lat));
          },
        }),
        ctx
      );

      ctx.save();

      ctx.beginPath();
      path(border);
      ctx.lineWidth = 0.5;
      ctx.strokeStyle = "#000";
      ctx.stroke();

      ctx.restore();
    }
  }
}
