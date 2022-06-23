<script>
  import { scaleLinear, min, max, extent } from "d3";

  export let width = 0;
  export let height = 0;

  export let bins = [];

  $: domain = [min(bins, (d) => d.lower), max(bins, (d) => d.upper)];
  $: range = extent(bins, (d) => d.value);

  $: x = scaleLinear(domain, [0, width]);
  $: y = scaleLinear(range, [height, 0]);
</script>

<svg viewBox="0 0 {width} {height}">
  {#each bins as bin}
    <rect
      x={x(bin.lower)}
      y={y(bin.value)}
      width={x(bin.upper) - x(bin.lower)}
      height={y(0) - y(bin.value)}
    />
  {/each}
</svg>
