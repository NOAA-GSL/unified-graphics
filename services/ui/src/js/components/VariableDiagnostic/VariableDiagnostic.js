import { Component, html } from "htm/preact";

export default class VariableDiagnostic extends Component {
  constructor() {
    super();

    this.state = { data: {} };

    fetch("/api/diag/wind/")
      .then((response) => response.json())
      .then((json) => this.setState({ data: json }));
  }

  render() {
    const features = this.state.data?.features ?? [];
    const guess = features.map((feature) => feature.properties.guess.magnitude);
    const analysis = features.map((feature) => feature.properties.analysis.magnitude);

    return html`<div class="flow">
      <h2>Wind</h2>

      <h3>Guess</h3>
      <div data-layout="cluster">
        <chart-map
          class="flex-1"
          data=${this.state.data}
          loop="guess"
          valueProperty="magnitude"
        ></chart-map>
        <chart-histogram
          class="flex-1"
          data=${guess}
          title-x="Observation − Forecast"
          title-y="Observation Count"
        ></chart-histogram>
      </div>

      <h3>Analysis</h3>
      <div data-layout="cluster">
        <chart-map
          class="flex-1"
          data=${this.state.data}
          loop="analysis"
          valueProperty="magnitude"
        ></chart-map>
        <chart-histogram
          class="flex-1"
          data=${analysis}
          title-x="Observation − Forecast"
          title-y="Observation Count"
        ></chart-histogram>
      </div>
    </div>`;
  }
}
