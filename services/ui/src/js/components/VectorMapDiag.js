import {
  extent,
  geoPath,
  geoTransform,
  interpolatePuOr,
  scaleDiverging,
  scaleLinear,
} from "d3";

export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <canvas></canvas>`;

  static #STYLE = `<style>
    :host {
      display: flex;
      flex-direction: column;
    }

    * {
      flex: 0 0 auto;
      margin: 0;
    }

    canvas {
      flex: 1 1 auto;
      aspect-ratio: 4 / 3;
    }
  </style>`;

  #data = {};

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = VectorMapDiag.#STYLE + VectorMapDiag.#TEMPLATE;
  }

  connectedCallback() {
    this.addEventListener("data-changed", this.update);
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

    if (obs && fcst) {
      const obsMinusFcst = obs.magnitude.map((magObs, idx) => [
        ...obs.coords[idx],
        magObs - fcst.magnitude[idx],
      ]);
      const [minDiff, maxDiff] = extent(obsMinusFcst, (d) => d[2]);
      const fill = scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff]);

      obsMinusFcst.forEach((omf) => {
        const [lng, lat, delta] = omf;

        ctx.beginPath();
        ctx.arc(x(lng - 360), y(lat), 6, 0, 2 * Math.PI);

        ctx.fillStyle = fill(delta);
        ctx.fill();
      });
    }

    if (obs) {
      ctx.beginPath();

      obs.direction.forEach((heading, idx) => {
        const [lng, lat] = obs.coords[idx];
        const heading_r = ((heading + 90) * Math.PI) / 180;
        // FIXME: This constant length should be configurable
        const dx = 12 * Math.cos(heading_r);
        const dy = 12 * Math.sin(heading_r);

        ctx.moveTo(x(lng - 360), y(lat));
        ctx.lineTo(x(lng - 360) + dx, y(lat) + dy);
      });

      ctx.stroke();
    }

    if (fcst) {
      ctx.beginPath();

      fcst.direction.forEach((heading, idx) => {
        const [lng, lat] = fcst.coords[idx];
        const heading_r = ((heading + 90) * Math.PI) / 180;
        // FIXME: This constant length should be configurable
        const dx = 8 * Math.cos(heading_r);
        const dy = 8 * Math.sin(heading_r);

        ctx.moveTo(x(lng - 360), y(lat));
        ctx.lineTo(x(lng - 360) + dx, y(lat) + dy);
      });

      ctx.strokeStyle = "#888888";
      ctx.stroke();
    }
  }
}
