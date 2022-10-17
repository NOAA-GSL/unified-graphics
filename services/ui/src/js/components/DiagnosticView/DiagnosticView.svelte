<script>
  import LoopDisplay from "./LoopDisplay.svelte";
  import { geoFilter } from "./DiagnosticView.helpers.js";

  /**
   * Brush event handler for ChartMap component
   *
   * @param {module:components/ChartMap#BrushEvent} event The brush event
   */
  function onBrush(event) {
    selection = event.detail;
  }

  let currentVariable = null;
  let selection = null;
  let variableType = "scalar";

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

  $: {
    featureCollection.then((data) => {
      variableType = data.features[0].properties.type;
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

{#await filtered}
  <p>Loading</p>
{:then data}
  <LoopDisplay {data} loop="guess" {variableType} {selection} on:chart-brush={onBrush}>
    <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
  </LoopDisplay>
  <LoopDisplay
    {data}
    loop="analysis"
    {variableType}
    {selection}
    on:chart-brush={onBrush}
  >
    <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
  </LoopDisplay>
{/await}
