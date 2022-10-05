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
  $: mapData = { type: "FeatureCollection", features: data };
  $: mapRadius =
    variableType === "vector"
      ? (d) => d.properties[loop].magnitude
      : (d) => d.properties[loop];
</script>

<slot name="title" />
<div data-layout="grid" class="flex-1" style="--row-size: minmax(20rem, 1fr)">
  <svelte:element
    this={distributionEl}
    data={distributionData}
    title-x="Direction (Observation − Forecast)"
    title-y="Magnitude (Observation − Forecast)"
  />
  <chart-map data={mapData} {selection} radius={mapRadius} />
</div>
