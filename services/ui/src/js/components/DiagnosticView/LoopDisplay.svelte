<script>
  export let data = [];
  export let selection = null;
  // FIXME: Should be an enum;
  export let loop = "guess";
  // FIXME: Should be an enum;
  export let variableType = "scalar";

  $: {
    console.log("LoopDisplay");
    console.log(data);
  }

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
<svelte:element
  this={distributionEl}
  class="flex-1"
  data={distributionData}
  title-x="Direction (Observation − Forecast)"
  title-y="Magnitude (Observation − Forecast)"
/>
<chart-map class="flex-1" data={mapData} {selection} radius={mapRadius} />
