<script>
  import Histogram from "./Histogram.svelte";

  export let title;
  export let observations;
  export let mean;
  export let std;
  export let bins;
</script>

<div>
  <h3>{title}</h3>
  <dl>
    <dt>Observations:</dt>
    <dd>{observations}</dd>
    <dt>Mean:</dt>
    <dd>{mean}</dd>
    <dt>Std. Dev.:</dt>
    <dd>{std}</dd>
  </dl>
  <Histogram {bins} />
</div>

<style lang="scss">
  div {
    aspect-ratio: 1/1;
  }
</style>
