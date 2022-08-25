import { html } from "htm/preact";
import { useState } from "preact/hooks";

import { geoFilter } from "./DiagnosticView.helpers";

export default function VectorVariable(props) {
  const [selection, setSelection] = useState(null);

  const brushCallback = (event) => {
    setSelection(event.detail);
  };

  const data = props.featureCollection.features.filter(geoFilter(selection));
  const guess = data.map((feature) => feature.properties.guess.magnitude);
  const analysis = data.map((feature) => feature.properties.analysis.magnitude);

  return html`<h2>Guess</h2>
    <div data-layout="cluster">
      <chart-histogram
        class="flex-1"
        data=${guess}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
      <chart-map
        class="flex-1"
        data=${props.featureCollection}
        selection=${selection}
        radius=${(feature) => feature.properties.guess.magnitude}
        onchart-brush=${brushCallback}
      ></chart-map>
    </div>

    <h2>Analysis</h2>
    <div data-layout="cluster">
      <chart-histogram
        class="flex-1"
        data=${analysis}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
      <chart-map
        class="flex-1"
        data=${props.featureCollection}
        selection=${selection}
        radius=${(feature) => feature.properties.analysis.magnitude}
        onchart-brush=${brushCallback}
      ></chart-map>
    </div>`;
}
