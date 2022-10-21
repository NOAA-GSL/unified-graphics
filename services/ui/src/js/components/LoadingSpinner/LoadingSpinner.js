export default class LoadingSpinner extends HTMLElement {
  static #STYLE = `:host {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .spinner {
      display: grid;
      grid-template-columns: 2rem 2rem;
      grid-template-rows: 2rem 2rem;
      gap: 0.25rem;
      transform: rotate(45deg) scale(66%);
    }

    .spinner div {
      background-color: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
    }

    .spinner div::after {
      content: "";
      display: block;
      background-color: currentColor;
      width: 100%;
      height: 100%;
      border-radius: 4px;
      animation: 2.5s ease-in-out var(--delay, 0s) infinite grow;
    }

    .spinner div:nth-child(1) {
      --delay: -1s;
    }

    .spinner div:nth-child(2) {
      --delay: -0.75s;
    }

    .spinner div:nth-child(4) {
      --delay: -0.5s;
    }

    .spinner div:nth-child(3) {
      --delay: -0.25s
    }

    @keyframes grow {
      0% {
        transform: scale(0%) rotate(0deg);
      }

      16% {
        transform: scale(100%) rotate(90deg);
      }

      50% {
        transform: scale(100%) rotate(90deg);
      }

      67% {
        transform: scale(0%) rotate(180deg);
      }

      100% {
        transform: scale(0%) rotate(180deg);
      }
    }`;

  static #TEMPLATE = `<div class="spinner">
    <div></div>
    <div></div>
    <div></div>
    <div></div>
  </div>
  <strong>
    <slot>LOADING</slot>
  </strong>`;

  constructor() {
    super();

    const root = this.attachShadow({ mode: "closed" });
    root.innerHTML = `<style>${LoadingSpinner.#STYLE}</style>${
      LoadingSpinner.#TEMPLATE
    }`;
  }
}
