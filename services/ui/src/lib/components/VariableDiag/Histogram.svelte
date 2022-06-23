<script>
  import { format, scaleLinear, min, max, extent } from "d3";

  export let width = 0;
  export let height = 0;

  export let bins = [];

  let margin = {
    top: 0,
    right: 0,
    bottom: 32,
    left: 0,
  };

  let formatNum = format("~s");

  $: domain = [min(bins, (d) => d.lower), max(bins, (d) => d.upper)];
  $: range = extent(bins, (d) => d.value);

  $: x = scaleLinear(domain, [margin.left, width - margin.left - margin.right]);
  $: y = scaleLinear(range, [height - margin.top - margin.bottom, margin.bottom]);
</script>

<svg viewBox="0 0 {width} {height}">
  {#each bins as bin}
    <rect
      class="bar"
      x={x(bin.lower)}
      y={y(bin.value)}
      width={x(bin.upper) - x(bin.lower)}
      height={y(0) - y(bin.value)}
    />
  {/each}
  <g class="x-axis" transform="translate({x(domain[0])}, {y(range[0])})">
    <path class="domain" d="M 1,8 l 0,-8 {x(domain[1]) - 2},0 0,8" />
    {#each x.ticks() as tick}
      <g class="tick" transform="translate({x(tick)}, 0)">
        <line y2="8" />
        <text y="10">{formatNum(tick)}</text>
      </g>
    {/each}
  </g>
</svg>

<style lang="scss">
  @use "uswds-core" as uswds;

  .domain {
    stroke-width: 2px;
    stroke: uswds.color("base-dark");
    fill: none;
  }

  .bar {
    fill: uswds.color("accent-cool-darker");
  }

  .tick {
    line {
      stroke: uswds.color("base-dark");
    }

    text {
      font-family: inherit;
      font-size: uswds.size("ui", "3xs");

      dominant-baseline: hanging;
      text-anchor: middle;
    }
  }
</style>
