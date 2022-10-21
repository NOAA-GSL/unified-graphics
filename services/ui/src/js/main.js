import App from "./App.svelte";

import Chart2DHistogram from "./components/Chart2DHistogram";
import ChartContainer from "./components/ChartContainer";
import ChartHistogram from "./components/ChartHistogram";
import ChartMap from "./components/ChartMap";
import LoadingSpinner from "./components/LoadingSpinner";

customElements.define("chart-2dhistogram", Chart2DHistogram);
customElements.define("chart-container", ChartContainer);
customElements.define("chart-histogram", ChartHistogram);
customElements.define("chart-map", ChartMap);
customElements.define("loading-spinner", LoadingSpinner);

const app = new App({
  target: document.body,
});

export default app;
