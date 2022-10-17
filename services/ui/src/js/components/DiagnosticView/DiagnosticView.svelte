<script>
  import LoopDisplay from "./LoopDisplay.svelte";

  let currentVariable = null;
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

{#await featureCollection}
  <p>Loading</p>
{:then data}
  <LoopDisplay {data} loop="guess" {variableType}>
    <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
  </LoopDisplay>
  <LoopDisplay {data} loop="analysis" {variableType}>
    <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
  </LoopDisplay>
{/await}
