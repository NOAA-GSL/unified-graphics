import { html } from "htm/preact";

import VariableDiagnostic from "../DiagnosticView";
import Header from "../Header";

const App = html`<${Header} />
  <main class="padding-x-3 padding-y-2">
    <${VariableDiagnostic} variable="wind" />
  </main>`;

export default App;
