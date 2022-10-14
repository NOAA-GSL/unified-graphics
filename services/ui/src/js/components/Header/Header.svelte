<!--
@component
The site header for the application.
-->
<header
  class="usa-dark-background text-base-lightest padding-y-2 padding-x-3"
  style="justify-content: space-between"
  data-layout="cluster"
>
  <h1 class="text-bold">Unified Graphics</h1>
  <form data-layout="cluster">
    <select class="usa-select">
      <option>RRFS</option>
    </select>
    <select class="usa-select">
      <option>05 May 2022 14:00</option>
    </select>
  </form>
  <nav>
    <!-- svelte-ignore a11y-no-redundant-roles -->
    <ul data-layout="cluster" role="list">
      <li>Diagnostics</li>
      <li>Model Output</li>
    </ul>
  </nav>
</header>
