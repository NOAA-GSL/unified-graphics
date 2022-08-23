import { html } from "htm/preact";

export default function Header() {
  return html`<header
    class="usa-dark-background display-flex flex-justify gap-2 padding-y-2 padding-x-3"
  >
    <strong><span>Unified Graphics</span></strong>
    <form class="display-flex gap-2">
      <select>
        <option>RRFS</option>
      </select>
      <select>
        <option>05 May 2022 14:00</option>
      </select>
    </form>
    <nav>
      <ul class="add-list-reset display-flex gap-2">
        <li><a href="#">Diagnostics</a></li>
        <li><a href="#">Model Output</a></li>
      </ul>
    </nav>
  </header>`;
}
