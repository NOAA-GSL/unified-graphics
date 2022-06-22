<script>
  import Histogram from "$lib/Histogram";

  let data = fetch("http://localhost:5000/diag/temperature").then((response) =>
    response.json()
  );
</script>

{#await data}
  <p>Loading</p>
{:then diag}
  <Histogram title="Temperature Guess" data={diag.guess.bins} />
  <Histogram title="Temperature Analysis" data={diag.analysis.bins} />
{:catch}
  <p>Oops</p>
{/await}
