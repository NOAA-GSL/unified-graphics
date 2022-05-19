<script>
  import "styles";
  import Header from "$lib/Header";
</script>

<Header />
<main>
  <slot />
</main>

<style lang="scss">
  main {
    flex-grow: 1;
    place-items: center;

    display: grid;
  }
</style>
