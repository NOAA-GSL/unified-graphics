<script>
  let currentVariable;

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
    {#await featureCollection}
      <p>Loading</p>
    {:then data}
      {#if data.features[0].properties.type === "vector"}
        <p>Vector display not implemented yet.</p>
      {:else}
        <p>Scalar display not implemented yet.</p>
      {/if}
    {/await}
  </div>
</div>
