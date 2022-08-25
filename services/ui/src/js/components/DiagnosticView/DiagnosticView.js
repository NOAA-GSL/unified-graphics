import { html } from "htm/preact";
import { useCallback, useEffect, useState } from "preact/hooks";

import useBrushedScalar from "./useBrushedScalar";
import VariableDisplay from "./VariableDisplay";

export default function DiagnosticView() {
  const [display, setDisplay] = useState(null);
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

  useEffect(() => {
    if (!display) return;
    fetch(`/api${display}/`)
      .then((response) => response.json())
      .then((json) => setFeatureCollection(json));
  }, [display]);

  useEffect(
    () =>
      fetch("/api/diag/")
        .then((response) => response.json())
        .then((json) => setVariables(json)),
    []
  );

  const brushCallback = (event) => {
    setSelection(event.detail);
    setGuessBrush(event.detail);
    setAnalysisBrush(event.detail);
  };

  const onVariableSelect = useCallback((event) => {
    setDisplay(event.target.value);
  });

  const options = Object.entries(variables).map(
    ([name, url]) => html`<option value=${url}>${name}</option>`
  );

  return html`<div class="flow">
    <select onChange=${onVariableSelect}>
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
