<script>
  export let diag_data = null;
  export let variableName = "";
  export let variableType = "scalar";

  let currentVariable = null;

  $: variables = fetch("/api/diag/")
    .then((response) => response.json())
    .then((json) => {
      currentVariable = json[0].url;
      return json;
    });

  $: init_times = currentVariable
    ? fetch(`/api${currentVariable}`)
        .then((response) => response.json())
        .then((json) => {
          const response = Object.entries(json).map(([name, url]) => ({ name, url }));
          diag_data = response[0].url;
          return response;
        })
    : Promise.resolve([]);

  $: {
    // Look up the name of the current variable based on its URL. The name is
    // needed for display in the LoopDisplay components.
    if (currentVariable) {
      variables.then((data) => {
        const variable = data.find(({ url }) => url === currentVariable);
        variableName = variable.name;
        variableType = variable.type;
      });
    }
  }
</script>

<!--
@component
The site header for the application.
-->
<header
  class="usa-dark-background text-base-lightest padding-y-2 padding-x-3"
  style="justify-content: space-between"
  data-layout="cluster"
>
  <h1 class="text-bold">Unified Graphics</h1>
  <form data-layout="cluster">
    <select class="usa-select" bind:value={currentVariable}>
      {#await variables then vars}
        {#each vars as variable}
          <option value={variable.url} data-type={variable.type}>{variable.name}</option
          >
        {/each}
      {/await}
    </select>

    <select class="usa-select" bind:value={diag_data}>
      {#await init_times then times}
        {#each times as time}
          <option value={time.url}>{time.name}</option>
        {/each}
      {/await}
    </select>
  </form>
  <nav>
    <!-- svelte-ignore a11y-no-redundant-roles -->
    <ul data-layout="cluster" role="list">
      <li>Diagnostics</li>
      <li>Model Output</li>
    </ul>
  </nav>
</header>
