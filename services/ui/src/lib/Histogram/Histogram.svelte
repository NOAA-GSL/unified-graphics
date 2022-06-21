<script>
  import { scaleLinear, min, max, extent } from "d3";

  /** @type string */
  export let title;

  export let data = [];

  $: domain = [min(data, (d) => d.lower), max(data, (d) => d.upper)];
  $: range = extent(data, (d) => d.value);

  $: x = scaleLinear(domain, [0, 300]);
  $: y = scaleLinear(range, [300, 0]);
</script>

<div>
  <strong>{title}</strong>
  <svg viewBox="0 0 300 300" width="300" height="300">
    {#each data as bin}
      <rect
        x={x(bin.lower)}
        y={y(bin.value)}
        width={x(bin.upper) - x(bin.lower)}
        height={y(0) - y(bin.value)}
      />
    {/each}
  </svg>
</div>
