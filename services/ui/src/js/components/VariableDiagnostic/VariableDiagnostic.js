import { html } from "htm/preact";
import { useEffect, useState } from "preact/hooks";

import useBrushedScalar from "./useBrushedScalar";

export default function VariableDiagnostic(props) {
  const [variables, setVariables] = useState({});
  const [selection, setSelection] = useState(null);
  const [featureCollection, setFeatureCollection] = useState({ features: [] });
  const [guess, setGuessBrush] = useBrushedScalar({
    features: featureCollection.features,
    loop: "guess",
    variable: "magnitude",
  });
  const [analysis, setAnalysisBrush] = useBrushedScalar({
    features: featureCollection.features,
    loop: "analysis",
    variable: "magnitude",
  });

  useEffect(
    () =>
      fetch(`/api/diag/${props.variable}/`)
        .then((response) => response.json())
        .then((json) => setFeatureCollection(json)),
    [props.variable]
  );

  useEffect(() =>
    fetch("/api/diag/")
      .then((response) => response.json())
      .then((json) => setVariables(json))
  );

  const brushCallback = (event) => {
    setSelection(event.detail);
    setGuessBrush(event.detail);
    setAnalysisBrush(event.detail);
  };

  const options = Object.entries(variables).map(
    ([name, url]) => html`<option value=${url}>${name}</option>`
  );

  return html`<div class="flow">
    <select>
      ${options}
    </select>

    <h3>Guess</h3>
    <div data-layout="cluster">
      <chart-histogram
        class="flex-1"
        data=${guess}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
      <chart-map
        class="flex-1"
        data=${featureCollection}
        loop="guess"
        selection=${selection}
        valueProperty="magnitude"
        onchart-brush=${brushCallback}
      ></chart-map>
    </div>

    <h3>Analysis</h3>
    <div data-layout="cluster">
      <chart-histogram
        class="flex-1"
        data=${analysis}
        title-x="Observation − Forecast"
        title-y="Observation Count"
      ></chart-histogram>
      <chart-map
        class="flex-1"
        data=${featureCollection}
        loop="analysis"
        selection=${selection}
        valueProperty="magnitude"
        onchart-brush=${brushCallback}
      ></chart-map>
    </div>
  </div>`;
}
