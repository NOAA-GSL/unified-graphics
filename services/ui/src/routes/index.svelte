<script>
  import { onMount } from "svelte";

  import Histogram from "$lib/Histogram";

  let data;

  $: if (data) {
    console.log(data);
  }

  onMount(async () => {
    data = await fetch("http://localhost:5000/diag/temperature").then((response) =>
      response.json()
    );
  });
</script>

<Histogram title="Temperature Guess" data={data?.guess?.bins} />
<Histogram title="Temperature Analysis" data={data?.analysis?.bins} />
