class DataSource extends HTMLElement {
  #data = null;

  static get observedAttributes() {
    return ["src"];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (name === "src" && oldValue !== newValue) {
      fetch(newValue)
        .then((response) => response.json())
        .then((data) => {
          this.#data = Object.freeze(data);
          this.onUpdate();
        });
    }
  }

  /**
   * @param {string|null} value
   */
  set src(value) {
    if (value) {
      this.setAttribute("src", value);
    } else {
      this.removeAttribute("src");
    }
  }

  /**
   * @return {string|null}
   */
  get src() {
    return this.getAttribute("src");
  }

  /**
   * @return {Object|null}
   */
  get data() {
    return this.#data ?? null;
  }

  onUpdate() {
    const event = new CustomEvent("data-changed", {
      bubbles: true,
      detail: this.data,
    });

    this.dispatchEvent(event);
  }
}

export default DataSource;
