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

export default class ChartMap extends HTMLElement {
  static #TEMPLATE = `<canvas></canvas>`;

  static #STYLE = `<style>
    :host {
      display: block;
    }

    canvas {
      aspect-ratio: 4 / 3;
      cursor: crosshair;
      width: 100%;
      height: 100%;
    }
  </style>`;

  #selection = null;
  #mousedownWrapper = null;
  #pendingUpdate = null;
  #borders = null;
  #data = null;

  static getObservedAttributes() {
    return ["loop", "value-property"];
  }

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = ChartMap.#STYLE + ChartMap.#TEMPLATE;
  }

  connectedCallback() {
    fetch("/geo/borders.json")
      .then((response) => response.json())
      .then((json) => {
        this.#borders = json;
        this.requestUpdate();
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
    const canvas = this.shadowRoot?.querySelector("canvas");

    if (canvas) {
      this.resizeObserver?.unobserve(canvas);
      canvas.removeEventListener("mousedown", this.#mousedownWrapper);
      this.#mousedownWrapper = null;
    }

    delete this.resizeObserver;
  }

  attributeChangedCallback() {
    this.requestUpdate();
  }

  get data() {
    return this.#data;
  }

  set data(value) {
    this.#data = value;
    this.requestUpdate();
  }

  get loop() {
    return this.getAttribute("loop");
  }

  set loop(value) {
    this.setAttribute("loop", value);
  }

  get valueProperty() {
    return this.getAttribute("value-property");
  }

  set valueProperty(value) {
    this.setAttribute("value-property", value);
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

    const borders = this.#borders;
    const observations = this.#data;

    if (!(borders || observations)) return;

    const projection = geoAlbers().fitSize([width, height], observations ?? borders);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const path = geoPath(projection, ctx);

    if (borders) {
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
      (feature) => feature.properties[this.loop][this.valueProperty]
    );

    const isDiverging = minDiff / Math.abs(minDiff) !== maxDiff / Math.abs(maxDiff);

    const fill = isDiverging
      ? scaleDiverging(interpolatePuOr).domain([minDiff, 0, maxDiff])
      : scaleSequential([minDiff, maxDiff], interpolatePurples);

    const r = scaleSqrt()
      .domain([0, Math.max(Math.abs(minDiff), Math.abs(maxDiff))])
      .range([0.5, 6]);

    observations.features.forEach((feature) => {
      const radius = r(Math.abs(feature.properties[this.loop][this.valueProperty]));
      const [x, y] = projection(feature.geometry.coordinates);

      ctx.save();
      ctx.fillStyle = fill(feature.properties[this.loop][this.valueProperty]);

      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fill();

      ctx.restore();
    });

    if (this.#selection) {
      const [upperLeft, lowerRight] = this.#selection;
      const [left, top] = projection.invert(upperLeft);
      const [right, bottom] = projection.invert(lowerRight);
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
