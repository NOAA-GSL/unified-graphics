<script>
  import Observations from "./Observations.svelte";

  export let title;
</script>

<article>
  <h2>{title}</h2>
  <Observations title="Observation - Background" />
  <Observations title="Observation - Analysis" />
</article>
