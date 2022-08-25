import { html } from "htm/preact";
import { useState } from "preact/hooks";

import useBrushedScalar from "./useBrushedScalar";
import VariableDisplay from "./VariableDisplay";

export default function ScalarVariable(props) {
  const [selection, setSelection] = useState(null);

  const [guess, setGuessBrush] = useBrushedScalar({
    features: props.featureCollection.features,
    loop: "guess",
  });
  const [analysis, setAnalysisBrush] = useBrushedScalar({
    features: props.featureCollection.features,
    loop: "analysis",
  });

  const brushCallback = (event) => {
    setSelection(event.detail);
    setGuessBrush(event.detail);
    setAnalysisBrush(event.detail);
  };

  return html` <h2>Guess</h2>
    <${VariableDisplay}
      loop="guess"
      distribution=${guess}
      observations=${props.featureCollection}
      selection=${selection}
      brushCallback=${brushCallback}
    />

    <h2>Analysis</h2>
    <${VariableDisplay}
      loop="analysis"
      distribution=${analysis}
      observations=${props.featureCollection}
      selection=${selection}
      brushCallback=${brushCallback}
    />`;
}
