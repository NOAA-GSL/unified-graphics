<script>
  export let data = [];
  export let selection = null;
  // FIXME: Should be an enum;
  export let loop = "guess";
  // FIXME: Should be an enum;
  export let variableType = "scalar";

  $: distributionEl =
    variableType === "vector" ? "chart-2dhistogram" : "chart-histogram";
  $: distributionData = data.map((d) => d.properties[loop]);
  $: xTitle =
    variableType === "vector"
      ? "Direction (Observation − Forecast)"
      : "Observation − Forecast";
  $: yTitle =
    variableType === "vector"
      ? "Magnitude (Observation − Forecast)"
      : "Observation count";
  $: mapData = { type: "FeatureCollection", features: data };
  $: mapRadius =
    variableType === "vector"
      ? (d) => d.properties[loop].magnitude
      : (d) => d.properties[loop];
</script>

<slot name="title" />
<div data-layout="grid" class="flex-1" style="--row-size: minmax(20rem, 1fr)">
  <chart-container>
    <span class="axis-y title" slot="title-y">{yTitle}</span>
    <svelte:element this={distributionEl} data={distributionData} />
    <span class="axis-x title" slot="title-x">{xTitle}</span>
  </chart-container>
  <chart-container>
    <chart-map data={mapData} {selection} radius={mapRadius} />
  </chart-container>
</div>
