function onChartBrush(event) {
  // Create a new set of search parameters with the currently selected model run from
  // our model form.
  const formData = new FormData(document.forms["model-form"]);
  let searchParams = new URLSearchParams(formData);

  for (let [key, value] of Object.entries(event.detail)) {
    // If this key has no value, we're done
    if (!value) continue;

    if (Array.isArray(value[0])) {
      // If the values are a mutlidimensional array, then we have a vector filter, and
      // each element of the outer array is a range of values for one component of the
      // vector, which needs to be added.
      for (let component of value) {
        searchParams.append(key, component.join("::"));
      }
    } else {
      // If we're not dealing with a multidimensional array, then we can just join the
      // components of this array.
      searchParams.append(key, value.join("::"));
    }
  }

  window.location.search = searchParams.toString();
}

document.addEventListener("chart-brush", onChartBrush);
