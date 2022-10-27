<script>
  import { range, region } from "./DiagnosticView.stores.js";
  import LoopDisplay from "./LoopDisplay.svelte";

  let currentVariable = null;
  let variableType = "scalar";
  let variableData = { features: [] };

  $: {
    // Clear the filters when currentVariable changes
    currentVariable;
    range.set(null);
    region.set(null);
  }

  $: variables = fetch("/api/diag/")
    .then((response) => response.json())
    .then((json) => {
      const response = Object.entries(json).map(([name, url]) => ({ name, url }));

      currentVariable = response[0].url;
      return response;
    });

  $: featureCollection = currentVariable
    ? fetch(`/api${currentVariable}`).then((response) => response.json())
    : new Promise(() => {});

  $: {
    featureCollection.then((data) => {
      variableType = data.features[0].properties.type;
      variableData = data;
    });
  }
</script>

<!--
@component
The DiagnosticView displays the distribution of values and location of
observations side-by-side for both the guess and analysis loops.
-->

<select class="usa-select" bind:value={currentVariable}>
  {#await variables then vars}
    {#each vars as variable}
      <option value={variable.url}>{variable.name}</option>
    {/each}
  {/await}
</select>

<div class="container flex-1" data-layout="stack">
  <div class="scroll-container flex-1" data-layout="stack">
    <LoopDisplay data={variableData} loop="guess" {variableType}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
    </LoopDisplay>
    <LoopDisplay data={variableData} loop="analysis" {variableType}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
    </LoopDisplay>
  </div>

  {#await featureCollection}
    <div class="overlay">
      <loading-spinner />
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
