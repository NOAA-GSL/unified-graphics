<script>
  import { containedIn, geoFilter } from "./DiagnosticView.helpers.js";
  import { filteredObservations, range, region } from "./DiagnosticView.stores.js";

  /** GeoJSON data for this loop */
  export let distribution = { features: [] };
  export let observations = { features: [] };

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

    let distRange = event.detail;

    if (variableType === "vector") {
      let [[x0, y0], [x1, y1]] = event.detail;

      distRange = {
        u: [x0, x1].sort(),
        v: [y0, y1].sort(),
      };
    }

    range.set(event.detail);
    region.set([
      [0, 0],
      [0, 0],
    ]);

    if (event.detail === null) {
      filteredObservations.set(new Set());
      return;
    }

    const filtered = distribution.features
      .filter(containedIn(distRange, loop))
      .map((feature) => feature.properties.stationId);

    filteredObservations.set(new Set(filtered));
  };

  /**
   * @param {CustomEvent} event
   */
  const onBrushMap = (event) => {
    event.stopImmediatePropagation();

    region.set(event.detail);
    range.set([0, 0]);

    if (
      event.detail === null ||
      event.detail[0][0] === event.detail[1][0] ||
      event.detail[0][1] === event.detail[1][1]
    ) {
      filteredObservations.set(new Set());
      return;
    }

    const filtered = observations.features
      .filter(geoFilter(event.detail))
      .map((feature) => feature.properties.stationId);

    filteredObservations.set(new Set(filtered));
  };

  $: distributionEl =
    variableType === "vector" ? "chart-2dhistogram" : "chart-histogram";

  $: distributionData = distribution.features
    .filter(
      (feature) =>
        $filteredObservations.size < 1 ||
        $filteredObservations.has(feature.properties.stationId)
    )
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
    features: observations.features.filter(
      (feature) =>
        $filteredObservations.size < 1 ||
        $filteredObservations.has(feature.properties.stationId)
    ),
  };

  $: mapRadius = (d) => d.properties[loop];

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
      data={distributionData}
      selection={$range}
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
      data={mapData}
      selection={$region}
      radius={mapRadius}
      on:chart-brush={onBrushMap}
    />
    <color-ramp slot="legend" for="observations-{loop}" class="font-ui-3xs" format="s"
      >{mapLegendTitle}</color-ramp
    >
  </chart-container>
</div>
