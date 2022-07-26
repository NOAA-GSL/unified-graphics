import { extent } from "d3-array";
import { scaleDiverging, scaleLinear } from "d3-scale";
import { interpolateRdBu } from "d3-scale-chromatic";
import { select } from "d3-selection";

import { zip } from "../utils";

export default class VectorMapDiag extends HTMLElement {
  static #TEMPLATE = `<slot name=title></slot>
  <svg></svg>`;

  static #STYLE = `<style>
    svg {
      aspect-ratio: 4 / 3;
    }
  </style>`;

  #data = {};

  constructor() {
    super();

    const shadowRoot = this.attachShadow({ mode: "open" });
    shadowRoot.innerHTML = VectorMapDiag.#STYLE + VectorMapDiag.#TEMPLATE;
  }

  set data(data) {
    this.#data = data;
    this.update();
  }

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "src") {
      fetch(newValue)
        .then((response) => response.json())
        .then((data) => {
          this.data = data;
        })
        .catch((reason) => {
          console.error(reason);
        });
    }
  }

  connectedCallback() {
    this.resizeObserver = new ResizeObserver(() => {
      this.update();
    });
    this.resizeObserver.observe(this.shadowRoot?.querySelector("svg"));
    this.update();
  }

  disconnectedCallback() {
    this.resizeObserver?.unobserve(this.shadowRoot?.querySelector("svg"));
    delete this.resizeObserver;
  }

  update() {
    const svg = select(this.shadowRoot).select("svg");
    const { height, width } = svg.node().getBoundingClientRect();

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const loop = this.#data.guess;

    if (!loop) return;

    const speed = [];
    for (const [obs, fcst, coord] of zip(
      loop.observation.magnitude,
      loop.forecast.magnitude,
      loop.coords
    )) {
      speed.push([...coord, obs - fcst]);
    }

    const x = scaleLinear(
      extent(speed, (d) => d[0]),
      [0, width]
    );
    const y = scaleLinear(
      extent(speed, (d) => d[1]),
      [height, 0]
    );

    const [minVal, maxVal] = extent(speed, (d) => d[2]);
    const fill = scaleDiverging([minVal, 0, maxVal], interpolateRdBu);

    svg
      .selectAll("circle")
      .data(speed)
      .join("circle")
      .attr("r", 4)
      .attr("cx", (d) => x(d[0]))
      .attr("cy", (d) => y(d[1]))
      .attr("fill", (d) => fill(d[2]));

    const obs = Array.from(zip(loop.observation.direction, loop.coords));

    svg
      .selectAll(".observation")
      .data(obs)
      .join("line")
      .attr("stroke", "black")
      .attr("stroke-width", "1px")
      .attr("x1", (d) => x(d[1][0]))
      .attr("y1", (d) => y(d[1][1]))
      .attr("x2", (d) => x(d[1][0]) + 12 * Math.cos(((d[0] + 90) * Math.PI) / 180))
      .attr("y2", (d) => y(d[1][1]) + 12 * Math.sin(((d[0] + 90) * Math.PI) / 180));

    const fcst = Array.from(zip(loop.forecast.direction, loop.coords));

    svg
      .selectAll(".forecast")
      .data(fcst)
      .join("line")
      .attr("stroke", "black")
      .attr("stroke-width", "1px")
      .attr("x1", (d) => x(d[1][0]))
      .attr("y1", (d) => y(d[1][1]))
      .attr("x2", (d) => x(d[1][0]) + 6 * Math.cos(((d[0] + 90) * Math.PI) / 180))
      .attr("y2", (d) => y(d[1][1]) + 6 * Math.sin(((d[0] + 90) * Math.PI) / 180));
  }
}
