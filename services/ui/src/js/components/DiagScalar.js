import { extent, max, scaleLinear } from "d3";
import ChartHistogram from "./Chart/ChartHistogram";

class DiagScalar extends HTMLElement {
  constructor() {
    super();

    const container = document.createElement("div");
    container.setAttribute("data-layout", "grid");

    this.guess = new ChartHistogram();
    this.analysis = new ChartHistogram();

    this.guess.titleX = this.analysis.titleX = "Observation − Forecast";
    this.guess.titleY = this.analysis.titleY = "Observation Count";
    this.guess.formatX = this.analysis.formatX = " ,.3f";

    container.appendChild(this.guess);
    container.appendChild(this.analysis);
    this.appendChild(container);
    this.addEventListener("data-load", this.dataLoadedCallback);
  }

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    this.guess.src = `${newValue}/ges/`;
    this.analysis.src = `${newValue}/anl/`;
  }

  dataLoadedCallback() {
    const domain = extent(this.guess.data.concat(this.analysis.data));
    const xScale = scaleLinear().domain(domain).nice(160);
    const thresholds = xScale.ticks(160);

    this.guess.thresholds = this.analysis.thresholds = thresholds;

    const range = [
      0,
      max(this.guess.bins.concat(this.analysis.bins), (bin) => bin.length),
    ];
    this.guess.range = this.analysis.range = range;
  }
}

export default DiagScalar;
