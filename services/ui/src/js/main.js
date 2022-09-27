import { render } from "preact";

import App from "./components/App";
import DataSource from "./components/DataSource";
import DiagScalar from "./components/DiagScalar";
import { Chart2DHistogram, ChartDensity, ChartHistogram } from "./components/Chart";
import ChartMap from "./components/ChartMap";

customElements.define("chart-2dhistogram", Chart2DHistogram);
customElements.define("chart-histogram", ChartHistogram);
customElements.define("chart-density", ChartDensity);
customElements.define("chart-map", ChartMap);
customElements.define("data-source", DataSource);
customElements.define("diag-scalar", DiagScalar);

render(App, document.body);
