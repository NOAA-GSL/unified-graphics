class ChartElement extends HTMLElement {
  #pendingUpdate = null;

  static get observedAttributes() {
    return ["width", "height"];
  }

  attributeChangedCallback(name) {
    switch (name) {
      case "height":
      case "width":
        this.update();
        break;
      default:
        break;
    }
  }

  get height() {
    const v = this.getAttribute("height");

    if (v) return +v;

    return undefined;
  }

  set height(value) {
    if (!value) {
      this.removeAttribute("height");
    } else {
      this.setAttribute("height", value.toString());
    }
  }

  get width() {
    const v = this.getAttribute("width");

    if (v) return +v;

    return undefined;
  }

  set width(value) {
    if (!value) {
      this.removeAttribute("width");
    } else {
      this.setAttribute("width", value.toString());
    }
  }

  update() {
    if (this.#pendingUpdate) return;

    this.#pendingUpdate = window.requestAnimationFrame(() => {
      this.#pendingUpdate = null;
      this.render();
    });
  }

  render() {}
}

export default ChartElement;
