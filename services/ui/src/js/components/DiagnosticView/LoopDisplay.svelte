<script>
  import { containedIn, geoFilter } from "./DiagnosticView.helpers.js";
  import { range, region } from "./DiagnosticView.stores.js";

  /** GeoJSON data for this loop */
  export let data = {};

  // FIXME: Should be an enum;
  /**
   * The loop to display.
   *
   * Should be either "guess" or "analysis" and should be a property present on
   * the `properties` object of each GeoJSON Feature.
   */
  export let loop = "guess";
  // FIXME: Should be an enum;
  /**
   * The variable type to display.
   *
   * Should be either "vector" or "scalar".
   */
  export let variableType = "scalar";

  /**
   * Handle range selection on histograms.
   *
   * @param {CustomEvent} event
   */
  const onBrushHistogram = (event) => {
    event.stopImmediatePropagation();
    range.set(event.detail);
  };

  /**
   * @param {CustomEvent} event
   */
  const onBrushMap = (event) => {
    event.stopImmediatePropagation();
    region.set(event.detail);
  };

  $: distributionEl =
    variableType === "vector" ? "chart-2dhistogram" : "chart-histogram";

  $: distributionData = data.features
    .filter(geoFilter($region))
    .map((d) => d.properties[loop]);

  $: xTitle =
    variableType === "vector"
      ? "Direction (Observation − Forecast)"
      : "Observation − Forecast";

  $: yTitle =
    variableType === "vector"
      ? "Magnitude (Observation − Forecast)"
      : "Observation count";

  $: mapData = {
    type: "FeatureCollection",
    features: data.features.filter(containedIn($range, loop)),
  };

  $: mapRadius =
    variableType === "vector"
      ? (d) => d.properties[loop].magnitude
      : (d) => d.properties[loop];
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
      data={distributionData}
      selection={$range}
      on:chart-brush={onBrushHistogram}
    />
    <span class="axis-x title" slot="title-x">{xTitle}</span>
  </chart-container>
  <chart-container>
    <chart-map
      data={mapData}
      selection={$region}
      radius={mapRadius}
      on:chart-brush={onBrushMap}
    />
  </chart-container>
</div>
