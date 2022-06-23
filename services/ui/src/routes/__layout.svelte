<script>
  import "styles";
  import Header from "$lib/components/Header";
</script>

<Header />
<main>
  <slot />
</main>

<style lang="scss">
  @use "uswds-core" as uswds;

  main {
    flex-grow: 1;
    grid-template-columns: repeat(
      auto-fit,
      minmax(min(uswds.units("mobile"), 100%), 1fr)
    );
    gap: uswds.units(2);
    align-items: start;

    display: grid;

    padding: uswds.units(2);

    overflow-x: hidden;
    overflow-y: auto;
  }
</style>
