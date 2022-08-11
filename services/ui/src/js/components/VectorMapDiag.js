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
    <div>
      <chart-histogram id="wind-speed" title-x="Wind Speed (Observation − Forecast)" title-y="Observation Count" format-x=" ,.3f"></chart-histogram>
      <chart-histogram id="wind-direction" title-x="Wind Direction (Observation − Forecast)" title-y="Observation Count" format-x=" ,.3f"></chart-histogram>
    </div>
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

  #data = {};
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
      const fill = scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff]).nice();
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

      const speedHist = this.shadowRoot?.querySelector("#wind-speed");
      const dirHist = this.shadowRoot?.querySelector("#wind-direction");
      if (speedHist || dirHist) {
        let speed = obsMinusFcst;
        let dir = obs.direction.map((dirObs, idx) => [
          ...obs.coords[idx],
          dirObs - fcst.direction[idx],
        ]);

        if (this.#selection) {
          const [x0, x1] = this.#selection.map((d) => x.invert(d[0]));
          const [y0, y1] = this.#selection.map((d) => y.invert(d[1]));

          const left = Math.min(x0, x1);
          const right = Math.max(x0, x1);
          const bottom = Math.min(y0, y1);
          const top = Math.max(y0, y1);

          const inSelection = (d) => {
            const lng = d[0] - 360;
            const lat = d[1];
            return lng >= left && lng <= right && lat >= bottom && lat <= top;
          };

          speed = speed.filter(inSelection);
          dir = dir.filter(inSelection);
        }

        if (speedHist) speedHist.data = speed.map((d) => d[2]);
        if (dirHist) dirHist.data = dir.map((d) => d[2]);
      }

      const start = fill.domain()[0],
        stop = fill.domain()[2];

      const legendX = scaleLinear()
        .domain([start, stop])
        .range([16, width / 2]);
      const step = (stop - start) / (width / 2 - 16);

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

    if (this.#selection) {
      const [[left, top], [right, bottom]] = this.#selection;

      ctx.globalAlpha = 0.5;
      ctx.fillStyle = "black";
      ctx.fillRect(left, top, right - left, bottom - top);
    }
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
