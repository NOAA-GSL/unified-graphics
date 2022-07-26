import styles from "../styles/_index.scss"; // eslint-disable-line

import ScalarVariableDiag from "./components/ScalarVariableDiag";
import ScalarLoopDiag from "./components/ScalarLoopDiag";

customElements.define("ug-diag-scalarvariable", ScalarVariableDiag);
customElements.define("ug-diag-scalarloop", ScalarLoopDiag);
