<script>
  import { range, region } from "./DiagnosticView.stores.js";
  import LoopDisplay from "./LoopDisplay.svelte";

  export let currentVariable = null;
  export let variableName = "";
  let variableType = "scalar";
  let guess = { features: [] };
  let analysis = { features: [] };

  $: {
    // Clear the filters when currentVariable changes
    currentVariable;
    range.set(null);
    region.set(null);
  }

  $: featureCollection = currentVariable
    ? Promise.all([
        fetch(`/api${currentVariable}ges/`).then((response) => response.json()),
        fetch(`/api${currentVariable}anl/`).then((response) => response.json()),
      ])
    : new Promise(() => [{}, {}]);

  $: {
    featureCollection.then(([ges, anl]) => {
      variableType = ges.features[0].properties.type;
      guess = ges;
      analysis = anl;
    });
  }
</script>

<!--
@component
The DiagnosticView displays the distribution of values and location of
observations side-by-side for both the guess and analysis loops.
-->

<div class="container flex-1" data-layout="stack">
  <div class="scroll-container flex-1" data-layout="stack">
    <LoopDisplay data={guess} loop="guess" {variableType} {variableName}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
    </LoopDisplay>
    <LoopDisplay data={analysis} loop="analysis" {variableType} {variableName}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
    </LoopDisplay>
  </div>

  {#await featureCollection}
    <div class="overlay">
      <loading-spinner class="text-accent-cool-darker" />
    </div>
  {/await}
</div>

<style>
  .container {
    contain: strict;
    position: relative;
  }

  .overlay {
    position: absolute;
    inset: 0;
    background-color: rgba(255, 255, 255, 0.5);

    display: grid;
    place-items: center;

    pointer-events: none;
  }
</style>
