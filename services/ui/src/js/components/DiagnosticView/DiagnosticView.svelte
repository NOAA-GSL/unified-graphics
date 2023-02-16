<script>
  import { range, region } from "./DiagnosticView.stores.js";
  import LoopDisplay from "./LoopDisplay.svelte";

  export let currentVariable = null;
  export let variableName = "";
  export let variableType = "scalar";

  let guessURL = "";
  let analysisURL = "";

  $: {
    // Clear the filters when currentVariable changes
    currentVariable;
    range.set(null);
    region.set(null);
  }

  $: if (currentVariable) {
    let base = `/api${currentVariable}`;
    let params = [];

    if ($region) {
      let lng = $region.map((d) => d[0]).join(",");
      let lat = $region.map((d) => d[1]).join(",");

      params.push(`longitude=${lng}`);
      params.push(`latitude=${lat}`);
    }

    if ($range) {
      params.push(`obs_minus_forecast_adjusted=${$range.join(",")}`);
    }

    const query = params.join("&");
    guessURL = [`${base}ges/`, query].join("?");
    analysisURL = [`${base}anl/`, query].join("?");
  }
</script>

<!--
@component
The DiagnosticView displays the distribution of values and location of
observations side-by-side for both the guess and analysis loops.
-->

<div class="container flex-1" data-layout="stack">
  <div class="scroll-container flex-1" data-layout="stack">
    <LoopDisplay src={guessURL} loop="guess" {variableName} {variableType}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Guess</h2>
    </LoopDisplay>
    <LoopDisplay src={analysisURL} loop="analysis" {variableName} {variableType}>
      <h2 slot="title" class="font-ui-lg text-bold grid-col-full">Analysis</h2>
    </LoopDisplay>
  </div>
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
