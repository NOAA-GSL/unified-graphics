import styles from "../styles/_index.scss"; // eslint-disable-line
import * as diag from "./diagnostics";

customElements.define("ug-diag-scalarvariable", diag.ScalarVariableDiag);
customElements.define("ug-diag-scalarloop", diag.ScalarLoopDiag);
