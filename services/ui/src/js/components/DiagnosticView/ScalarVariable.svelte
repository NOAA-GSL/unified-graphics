<script>
  import { geoFilter } from "./DiagnosticView.helpers.js";

  export let data = [];

  let selection = null;

  function onBrush(event) {
    selection = event.detail;
  }

  $: filtered = data.features.filter(geoFilter(selection));
  $: guess = filtered.map((feature) => feature.properties.guess);
  $: analysis = filtered.map((feature) => feature.properties.analysis);
</script>

<h2 class="font-ui-lg text-bold grid-col-full">Guess</h2>
<chart-histogram
  class="flex-1"
  data={guess}
  title-x="Observation − Forecast"
  title-y="Observation Count"
/>
<chart-map
  class="flex-1"
  {data}
  {selection}
  radius={(feature) => feature.properties.guess}
  on:chart-brush={onBrush}
/>

<h2 class="font-ui-lg text-bold grid-col-full">Analysis</h2>
<chart-histogram
  class="flex-1"
  data="${analysis}"
  title-x="Observation − Forecast"
  title-y="Observation Count"
/>
<chart-map
  class="flex-1"
  {data}
  {selection}
  radius={(feature) => feature.properties.analysis}
  on:chart-brush={onBrush}
/>
