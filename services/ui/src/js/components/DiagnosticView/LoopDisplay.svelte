<script>
  import { range, region } from "./DiagnosticView.stores.js";

  export let src = null;

  export let loop = "ges";

  // FIXME: Should be an enum;
  /**
   * The variable type to display.
   *
   * Should be either "vector" or "scalar".
   */
  export let variableType = "scalar";

  /**
   * The name of the variable on display.
   */
  export let variableName = "";

  /**
   * Handle range selection on histograms.
   *
   * @param {CustomEvent} event
   */
  const onBrushHistogram = (event) => {
    event.stopImmediatePropagation();
    region.set(null);
    range.set(event.detail);
  };

  /**
   * @param {CustomEvent} event
   */
  const onBrushMap = (event) => {
    event.stopImmediatePropagation();
    range.set([0, 0]);
    region.set(event.detail);
  };

  $: distributionEl =
    variableType === "vector" ? "chart-2dhistogram" : "chart-histogram";

  $: xTitle =
    variableType === "vector"
      ? "Direction (Observation − Forecast)"
      : "Observation − Forecast";

  $: yTitle =
    variableType === "vector"
      ? "Magnitude (Observation − Forecast)"
      : "Observation count";

  $: mapRadius =
    variableType === "vector"
      ? (d) => d.properties["adjusted"].magnitude
      : (d) => d.properties["adjusted"];

  $: mapLegendTitle = variableName === "wind" ? `${variableName} speed` : variableName;
</script>

<!--
@component
The LoopDisplay shows the distribution of values and the location of
observations for a single loop from model initialization. The chart type for
the distribution is based on whether the variable being displayed is a vector
or a scalar variable. For vectors, we use a heatmap; for scalars, we use a
histogram.

Slots:
- **title**: Title for the loop display

Usage:
```
<LoopDisplay data={geojson} loop="guess" variableType="vector">
  <h2 slot="title">Guess</h2>
</LoopDisplay>
```
-->
<slot name="title" />
<div data-layout="grid" class="flex-1" style="--row-size: minmax(20rem, 1fr)">
  <chart-container>
    <span class="axis-y title" slot="title-y">{yTitle}</span>
    <svelte:element
      this={distributionEl}
      id="distribution-{loop}"
      {src}
      selection={$range}
      format-x=".3e"
      on:chart-brush={onBrushHistogram}
    />
    <span class="axis-x title" slot="title-x">{xTitle}</span>
    {#if variableType === "vector"}
      <color-ramp slot="legend" for="distribution-{loop}" class="font-ui-3xs"
        >Observation Count</color-ramp
      >
    {/if}
  </chart-container>
  <chart-container>
    <chart-map
      id="observations-{loop}"
      {src}
      selection={$region}
      radius={mapRadius}
      on:chart-brush={onBrushMap}
    />
    <color-ramp slot="legend" for="observations-{loop}" class="font-ui-3xs" format="s"
      >{mapLegendTitle}</color-ramp
    >
  </chart-container>
</div>
