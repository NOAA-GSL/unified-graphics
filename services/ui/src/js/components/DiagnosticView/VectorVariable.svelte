<script>
  import { geoFilter } from "./DiagnosticView.helpers";

  export let data = {};

  let selection = null;

  $: filtered = data.features.filter(geoFilter(selection));
  $: guess = filtered.map((feature) => feature.properties.guess);
  $: analysis = filtered.map((feature) => feature.properties.analysis);

  function onBrush(event) {
    selection = event.detail;
  }
</script>

<h2 class="font-ui-lg text-bold grid-col-full">Guess</h2>
<chart-2dhistogram
  class="flex-1"
  data={guess}
  title-x="Direction (Observation − Forecast)"
  title-y="Magnitude (Observation − Forecast)"
/>
<chart-map
  class="flex-1"
  {data}
  {selection}
  radius={(feature) => feature.properties.guess.magnitude}
  on:chart-brush={onBrush}
/>

<h2 class="font-ui-lg text-bold grid-col-full">Analysis</h2>
<chart-2dhistogram
  class="flex-1"
  data={analysis}
  title-x="Direction (Observation − Forecast)"
  title-y="Magnitude (Observation − Forecast)"
/>
<chart-map
  class="flex-1"
  {data}
  {selection}
  radius={(feature) => feature.properties.analysis.magnitude}
  on:chart-brush={onBrush}
/>
