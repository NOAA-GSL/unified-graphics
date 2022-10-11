import App from "./App.svelte";

import { Chart2DHistogram, ChartHistogram } from "./components/Chart";
import ChartMap from "./components/ChartMap";

customElements.define("chart-2dhistogram", Chart2DHistogram);
customElements.define("chart-histogram", ChartHistogram);
customElements.define("chart-map", ChartMap);

const app = new App({
  target: document.body,
});

export default app;
