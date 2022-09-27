import { html } from "htm/preact";

export default function Header() {
  return html`<header
    class="usa-dark-background text-base-lightest padding-y-2 padding-x-3"
    style="justify-content: space-between"
    data-layout="cluster"
  >
    <h1 class="text-bold">Unified Graphics</h1>
    <form data-layout="cluster">
      <select>
        <option>RRFS</option>
      </select>
      <select>
        <option>05 May 2022 14:00</option>
      </select>
    </form>
    <nav>
      <ul data-layout="cluster" role="list">
        <li><a href="#">Diagnostics</a></li>
        <li><a href="#">Model Output</a></li>
      </ul>
    </nav>
  </header>`;
}
