<script>
  import { format } from "d3";

  import Histogram from "./Histogram.svelte";

  export let title;
  export let observations;
  export let mean;
  export let std;
  export let bins;
  export let domain;
  export let range;

  let width;
  let height;

  const formatNum = format(",");
  const formatDecimal = format(",.3f");
</script>

<div class="container aspect-square flow">
  <h3>{title}</h3>
  <dl>
    <div>
      <dt>Observations:</dt>
      <dd>{formatNum(observations)}</dd>
    </div>
    <div>
      <dt>Mean:</dt>
      <dd>{formatDecimal(mean)}</dd>
    </div>
    <div>
      <dt>Std. Dev.:</dt>
      <dd>{formatDecimal(std)}</dd>
    </div>
  </dl>

  <div class="overflow-hidden" bind:offsetWidth={width} bind:offsetHeight={height}>
    <Histogram {width} {height} {bins} {domain} {range} />
  </div>
</div>

<style lang="scss">
  @use "uswds-core" as uswds;

  .container {
    --space: #{uswds.units("05")};

    flex: 1 1 0;
    flex-direction: column;

    display: flex;

    font-size: uswds.size("ui", "2xs");

    > * {
      flex: 1 1 auto;
    }

    > h3,
    > dl {
      flex: 0 0 auto;
    }
  }

  h3 {
    font-size: uswds.size("ui", "sm");
  }

  dt,
  dd {
    display: inline-block;
  }

  dt {
    font-weight: bold;
  }
</style>
