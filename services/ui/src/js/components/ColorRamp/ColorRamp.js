/** @module components/ColorRamp */

export default class ColorRamp extends HTMLElement {
  static #TEMPLATE = `<slot></slot>
    <svg viewBox="0 0 300 16"></svg>`;

  static #STYLE = `:host {
    display: flex;
    flex-direction: column;
  }

  svg {
    flex-grow: 1;
  }`;

  constructor() {
    super();

    const root = this.attachShadow({ mode: "closed" });
    root.innerHTML = `<style>${ColorRamp.#STYLE}</style>${ColorRamp.#TEMPLATE}`;
  }
}
