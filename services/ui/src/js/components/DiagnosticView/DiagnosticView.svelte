<script>
  import { range, region } from "./DiagnosticView.stores.js";
  import LoopDisplay from "./LoopDisplay.svelte";

  export let currentVariable = null;
  export let variableName = "";
  export let variableType = "scalar";

  $: {
    // Clear the filters when currentVariable changes
    currentVariable;
    range.set(null);
    region.set(null);
  }

  $: guessURL = `/api${currentVariable}ges/`;
  $: analysisURL = `/api${currentVariable}anl/`;
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
