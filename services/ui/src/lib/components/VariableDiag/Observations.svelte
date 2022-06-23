<script>
  import { format } from "d3";

  import Histogram from "./Histogram.svelte";

  export let title;
  export let observations;
  export let mean;
  export let std;
  export let bins;

  const formatNum = format(",");
  const formatDecimal = format(",.3f");
</script>

<div class="aspect-square">
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
  <Histogram {bins} />
</div>

<style lang="scss">
  dt,
  dd {
    display: inline-block;
  }

  dt {
    font-weight: bold;
  }
</style>
