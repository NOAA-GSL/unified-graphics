<script>
  import { format, scaleLinear } from "d3";

  export let width = 0;
  export let height = 0;

  export let bins = [];
  export let domain;
  export let range;

  let margin = {
    top: 0,
    right: 0,
    bottom: 32,
    left: 0,
  };

  let formatNum = format("~s");

  $: x = scaleLinear(domain, [margin.left, width - margin.left - margin.right]);
  $: y = scaleLinear(range, [height - margin.top - margin.bottom, margin.bottom]);

  $: bars = bins
    .map((bin) => ({
      x: x(bin.lower),
      y: y(bin.value),
      width: x(bin.upper) - x(bin.lower),
      height: y(0) - y(bin.value),
    }))
    .filter((bar) => bar.height >= 1);
</script>

<svg viewBox="0 0 {width} {height}">
  <g class="y-axis" transform="translate({x(domain[0])}, {margin.top})">
    {#each y.ticks() as tick}
      <g class="tick" transform="translate(0, {y(tick)})">
        <line x2={x(domain[1])} />
        <text dy="-4">{formatNum(tick)}</text>
      </g>
    {/each}
  </g>

  {#each bars as bar}
    <rect class="bar" x={bar.x} y={bar.y} width={bar.width} height={bar.height} />
  {/each}

  <g class="x-axis" transform="translate({x(domain[0])}, {y(range[0]) + 1})">
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
    }
  }

  .x-axis .tick text {
    dominant-baseline: hanging;
    text-anchor: middle;
  }
</style>
