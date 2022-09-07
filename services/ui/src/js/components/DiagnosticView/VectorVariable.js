import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { geoFilter } from "./DiagnosticView.helpers";

export default function VectorVariable(props) {
  const [selection, setSelection] = useState(null);

  const brushCallback = (event) => {
    setSelection(event.detail);
  };

  const data = props.featureCollection.features.filter(geoFilter(selection));
  const guess = data.map((feature) => feature.properties.guess);
  const analysis = data.map((feature) => feature.properties.analysis);

  return html`<h2 data-colspan="full">Guess</h2>
    <chart-2dhistogram
      class="flex-1"
      data=${guess}
      title-x="Direction (Observation − Forecast)"
      title-y="Magnitude (Observation − Forecast)"
    ></chart-density>
    <chart-map
      class="flex-1"
      data=${props.featureCollection}
      selection=${selection}
      radius=${(feature) => feature.properties.guess.magnitude}
      onchart-brush=${brushCallback}
    ></chart-map>

    <h2 data-colspan="full">Analysis</h2>
    <chart-2dhistogram
      class="flex-1"
      data=${analysis}
      title-x="Direction (Observation − Forecast)"
      title-y="Magnitude (Observation − Forecast)"
    ></chart-density>
    <chart-map
      class="flex-1"
      data=${props.featureCollection}
      selection=${selection}
      radius=${(feature) => feature.properties.analysis.magnitude}
      onchart-brush=${brushCallback}
    ></chart-map>`;
}
