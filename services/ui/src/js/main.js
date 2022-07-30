import styles from "../styles/_index.scss"; // eslint-disable-line

import DataSource from "./components/DataSource";
import ScalarVariableDiag from "./components/ScalarVariableDiag";
import ScalarLoopDiag from "./components/ScalarLoopDiag";
import VectorMapDiag from "./components/VectorMapDiag";

customElements.define("data-source", DataSource);
customElements.define("ug-diag-scalarvariable", ScalarVariableDiag);
customElements.define("ug-diag-scalarloop", ScalarLoopDiag);
customElements.define("diag-vectormap", VectorMapDiag);
