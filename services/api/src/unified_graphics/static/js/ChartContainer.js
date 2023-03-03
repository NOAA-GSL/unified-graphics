/**
 * Containing element that automatically resizes the elements in its default
 * slot.
 *
 * This component uses a ResizeObserver and a MutationObserver to set the
 * `width` and `height` properties on whatever elements are in the default
 * slot whenever the container is resized, or the children change.
 *
 * It provides slots for inserting axis title for the x- and y-axes called
 * "title-x" and "title-y" respectively.
 *
 * @example
 * <chart-container>
 *   <span slot="title-y">Y Axis Title</span>
 *   <chart-histogram></chart-histogram>
 *   <span slot="title-x">X Axis Title</span>
 * <chart-container>
 */
class ChartContainer extends HTMLElement {
  static #TEMPLATE = `<slot name=title-y></slot>
    <div class=container><slot></slot></div>
    <slot name=title-x></slot>
    <slot name=legend></slot>`;

  static #STYLE = `:host {
    display: grid;
    grid-template-columns: min-content 1fr;
    grid-template-rows: 1fr repeat(2, min-content);
    grid-template-areas:
      "title-y container"
      "....... title-x"
      "....... legend";
  }

  :host,
  .container {
    contain: strict;
  }

  .container {
    grid-area: container;
  }

  ::slotted([slot*=title]) {
    text-align: center;
  }

  ::slotted([slot=title-x]) {
    grid-area: title-x;
  }

  ::slotted([slot=title-y]) {
    grid-area: title-y;
    writing-mode: vertical-rl;
    transform: rotate(180deg);
  }

  ::slotted([slot=legend]) {
    grid-area: legend;
  }`;

  #resizeObserver = null;
  #mutationObserver = null;
  #container = null;

  constructor() {
    super();

    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>${ChartContainer.#STYLE}</style>
      ${ChartContainer.#TEMPLATE}`;

    this.#container = this.shadowRoot.querySelector(".container");
  }

  connectedCallback() {
    this.#resizeObserver = new ResizeObserver(() => {
      this.#resized();
    });

    this.#resizeObserver.observe(this.#container);

    this.#mutationObserver = new MutationObserver(() => {
      this.#resized();
    });

    this.#mutationObserver.observe(this, {
      childList: true,
      attributes: false,
      subtree: false,
    });
  }

  disconnectedCallback() {
    this.#resizeObserver.unobserve(this.#container);
    this.#mutationObserver.disconnect(this);
  }

  #resized() {
    const { width, height } = this.#container.getBoundingClientRect();

    for (const child of this.querySelectorAll(":not([slot])")) {
      if (child.localName.includes("-")) {
        // If this is a custom element, make sure we wait until it's defined
        // before setting the width and height. There can be a race condition
        // where ChartContainer elements are upgraded before their children, and
        // then setting width and height on the children shadows the getters and
        // setters on the custom element. If the setter doesn't run,
        // setAttribute is never called and the elements never re-render.
        customElements.whenDefined(child.localName).then(() => {
          Object.assign(child, { width, height });
        });
      } else {
        Object.assign(child, { width, height });
      }
    }
  }
}

customElements.define("chart-container", ChartContainer);
