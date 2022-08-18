import { html } from "htm/preact";

export default function Header() {
  return html`<header
    class="usa-dark-background display-flex flex-justify-center padding-y-2 padding-x-3"
  >
    <strong>Unified Graphics</strong>
    <select>
      <option>RRFS</option>
    </select>
    <select>
      <option>05 May 2022 14:00</option>
    </select>
  </header>`;
}
