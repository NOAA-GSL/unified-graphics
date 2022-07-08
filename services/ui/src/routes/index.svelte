<script>
  import VariableDiag from "$lib/components/VariableDiag";
  import api from "$lib/helpers/api.helper";

  let data = api.diagnostics();
</script>

{#await data}
  <p>Loading</p>
{:then diag}
  <VariableDiag title="Temperature" {...diag} />
{:catch}
  <p>Oops</p>
{/await}
