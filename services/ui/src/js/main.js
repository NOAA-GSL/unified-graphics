import { render } from "preact";

import styles from "../styles/_index.scss"; // eslint-disable-line

import App from "./components/App";
import DataSource from "./components/DataSource";
import DiagScalar from "./components/DiagScalar";
import Histogram from "./components/Histogram";
import ChartDensity from "./components/ChartDensity";
import ChartMap from "./components/ChartMap";

customElements.define("chart-histogram", Histogram);
customElements.define("chart-density", ChartDensity);
customElements.define("chart-map", ChartMap);
customElements.define("data-source", DataSource);
customElements.define("diag-scalar", DiagScalar);

render(App, document.body);
