function onChartBrush(event) {
  let { searchParams } = new URL(window.location);

  for (let [key, value] of Object.entries(event.detail)) {
    if (!value) {
      searchParams.delete(key);
      continue;
    }

    searchParams.set(key, value.join("::"));
  }

  window.location.search = searchParams.toString();
}

document.addEventListener("chart-brush", onChartBrush);
