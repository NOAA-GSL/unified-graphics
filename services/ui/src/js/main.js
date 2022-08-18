import styles from "../styles/_index.scss"; // eslint-disable-line

import DataSource from "./components/DataSource";
import DiagScalar from "./components/DiagScalar";
import Histogram from "./components/Histogram";
import VectorMapDiag from "./components/VectorMapDiag";

import App from "./components/App";
import { render } from "preact";

customElements.define("chart-histogram", Histogram);
customElements.define("data-source", DataSource);
customElements.define("diag-scalar", DiagScalar);
customElements.define("diag-vectormap", VectorMapDiag);

render(App, document.body);
