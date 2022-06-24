<script>
  import VariableDiag from "$lib/components/VariableDiag";

  let data = fetch("http://localhost:5000/diag/temperature").then((response) =>
    response.json()
  );
</script>

{#await data}
  <p>Loading</p>
{:then diag}
  <VariableDiag title="Temperature" {...diag} />
{:catch}
  <p>Oops</p>
{/await}
