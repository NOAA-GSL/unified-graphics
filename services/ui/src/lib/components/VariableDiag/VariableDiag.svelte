<script>
  import { extent, max, min } from "d3";

  import Observations from "./Observations.svelte";

  export let title;
  export let guess;
  export let analysis;

  let domain = [0, 1];
  let range = [0, 1];

  $: if (guess && analysis) {
    const bins = guess.bins.concat(analysis.bins);

    domain = [min(bins, (d) => d.lower), max(bins, (d) => d.upper)];
    range = extent(bins, (d) => d.value);
  }
</script>

<article class="flow">
  <h2>{title}</h2>
  <div data-layout="cluster">
    <Observations title="Observation - Background" {...guess} {domain} {range} />
    <Observations title="Observation - Analysis" {...analysis} {domain} {range} />
  </div>
</article>

<style lang="scss">
  @use "uswds-core" as uswds;

  article {
    --space: #{uswds.units(1)};
  }
</style>
