<script>
  export let title;
  export let observations;
  export let mean;
  export let std;
  export let bins;
</script>

<div>
  <h3>{title}</h3>
  <dl>
    <dt>Observations:</dt>
    <dd>{observations}</dd>
    <dt>Mean:</dt>
    <dd>{mean}</dd>
    <dt>Std. Dev.:</dt>
    <dd>{std}</dd>
  </dl>
</div>
