import { html } from "htm/preact";

export default function VariableDisplay(props) {
  return html`<div data-layout="cluster">
    <chart-histogram
      class="flex-1"
      data=${props.distribution}
      title-x="Observation − Forecast"
      title-y="Observation Count"
    ></chart-histogram>
    <chart-map
      class="flex-1"
      data=${props.observations}
      loop=${props.loop}
      selection=${props.selection}
      valueProperty="magnitude"
      onchart-brush=${props.brushCallback}
    ></chart-map>
  </div>`;
}
