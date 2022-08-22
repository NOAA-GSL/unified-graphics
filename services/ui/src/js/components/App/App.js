import { html } from "htm/preact";

import VariableDiagnostic from "../VariableDiagnostic";
import Header from "../Header";

const App = html`<${Header} />
  <main>
    <${VariableDiagnostic} variable="wind" />
  </main>`;

export default App;
