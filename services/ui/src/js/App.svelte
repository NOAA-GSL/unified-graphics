<script>
  import DiagnosticView from "./components/DiagnosticView";
  import Header from "./components/Header";

  let url = null;
  let name = "";
  let variableType = "scalar";
</script>

<!--
@component
The root component for the application.
-->
<Header bind:diag_data={url} bind:variableName={name} bind:variableType />

<main class="padding-x-3 padding-y-2" data-layout="stack">
  <DiagnosticView currentVariable={url} variableName={name} {variableType} />
</main>
