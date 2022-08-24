import { html } from "htm/preact";
import { useEffect, useState } from "preact/hooks";

import useBrushedScalar from "./useBrushedScalar";
import VariableDisplay from "./VariableDisplay";

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

    <h2>Guess</h2>
    <${VariableDisplay}
      loop="guess"
      distribution=${guess}
      observations=${featureCollection}
      selection=${selection}
      brushCallback=${brushCallback}
    />

    <h2>Analysis</h2>
    <${VariableDisplay}
      loop="analysis"
      distribution=${analysis}
      observations=${featureCollection}
      selection=${selection}
      brushCallback=${brushCallback}
    />
  </div>`;
}
