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
      <strong>Wind</strong>
      <chart-histogram
        data=${guess}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
      <chart-histogram
        data=${analysis}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
    </div>`;
  }
}
