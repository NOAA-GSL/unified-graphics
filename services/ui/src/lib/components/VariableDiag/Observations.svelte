<script>
  import { format } from "d3";

  import Histogram from "./Histogram.svelte";

  export let title;
  export let observations;
  export let mean;
  export let std;
  export let bins;

  let width;
  let height;

  const formatNum = format(",");
  const formatDecimal = format(",.3f");
</script>

<div class="container aspect-square">
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
    <Histogram {width} {height} {bins} />
  </div>
</div>

<style lang="scss">
  .container {
    flex: 1 1 0;
    flex-direction: column;

    display: flex;

    > * {
      flex: 1 1 auto;
    }

    > h3,
    > dl {
      flex: 0 0 auto;
    }
  }

  dt,
  dd {
    display: inline-block;
  }

  dt {
    font-weight: bold;
  }
</style>
