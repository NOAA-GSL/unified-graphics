/**
 * A class representing margins in a chart.
 *
 * This class is constructed following the convention for the `margin` shorthand CSS property.
 *
 * @property {number} top - The top margin in pixels
 * @property {number} right - The right margin in pixels
 * @property {number} bottom - The bottom margin in pixels
 * @property {number} left - The left margin in pixels
 * @readonly
 * @property {number} horizontal - The total horizontal margin (left + right)
 * @readonly
 * @property {number} vertical - The total vertical margin (top + bottom)
 */
export default class Margin {
  constructor(top, right, bottom, left) {
    this.top = top || 0;
    this.right = right || this.top;
    this.bottom = bottom || this.top;
    this.left = left || this.right;
  }

  get horizontal() {
    return this.left + this.right;
  }

  get vertical() {
    return this.top + this.bottom;
  }
}
