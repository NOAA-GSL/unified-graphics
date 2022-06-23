<script>
  import Observations from "./Observations.svelte";

  export let title;
  export let guess;
  export let analysis;
</script>

<article>
  <h2>{title}</h2>
  <div data-layout="cluster">
    <Observations title="Observation - Background" {...guess} />
    <Observations title="Observation - Analysis" {...analysis} />
  </div>
</article>
