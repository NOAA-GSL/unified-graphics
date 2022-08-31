import { html } from "htm/preact";
import { useCallback, useEffect, useState } from "preact/hooks";

import ScalarVariable from "./ScalarVariable";
import VectorVariable from "./VectorVariable";

export default function DiagnosticView() {
  const [display, setDisplay] = useState(null);
  const [variables, setVariables] = useState([]);
  const [featureCollection, setFeatureCollection] = useState({ features: [] });

  useEffect(() => {
    fetch("/api/diag/")
      .then((response) => response.json())
      .then((json) => {
        const entries = Object.entries(json);
        setVariables(entries);
        setDisplay(entries[0][1]);
      });
  }, []);

  useEffect(() => {
    if (!display) return;
    fetch(`/api${display}/`)
      .then((response) => response.json())
      .then((json) => setFeatureCollection(json));
  }, [display]);

  const onVariableSelect = useCallback((event) => {
    setDisplay(event.target.value);
  }, []);

  const VariableComponent =
    featureCollection.features[0]?.properties?.type === "vector"
      ? VectorVariable
      : ScalarVariable;

  const options = variables.map(
    ([name, url]) => html`<option value=${url}>${name}</option>`
  );

  return html`<div class="flow">
    <select onChange=${onVariableSelect}>
      ${options}
    </select>

    <${VariableComponent} featureCollection=${featureCollection} />
  </div>`;
}
