<script>
  import LoopDisplay from "./LoopDisplay.svelte";
  import { geoFilter } from "./DiagnosticView.helpers.js";

  function onBrush(event) {
    selection = event.detail;
  }

  let currentVariable = null;
  let selection = null;

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

  $: filtered = featureCollection.then((data) =>
    data.features.filter(geoFilter(selection))
  );
</script>

<div class="flow">
  <select class="usa-select" bind:value={currentVariable}>
    {#await variables then vars}
      {#each vars as variable}
        <option value={variable.url}>{variable.name}</option>
      {/each}
    {/await}
  </select>

  <div data-layout="grid">
    {#await filtered}
      <p>Loading</p>
    {:then data}
      <LoopDisplay {data} loop="guess" {selection} on:chart-brush={onBrush}>
        <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
      </LoopDisplay>
      <LoopDisplay {data} loop="analysis" {selection} on:chart-brush={onBrush}>
        <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
      </LoopDisplay>
    {/await}
  </div>
</div>
