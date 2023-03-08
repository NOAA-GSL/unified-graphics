/** @module helpers */

import { range, scaleThreshold } from "../vendor/d3.js";

/**
 * @typedef {Array.<number>} TwoDBin
 * @property {number} x0 The lower bound of the bin on the x-axis
 * @property {number} x1 The upper bound of the bin on the x-axis
 * @property {number} y0 The lower bound of the bin on the y-axis
 * @property {number} y1 The upper bound of the bin on the y-axis
 */

/**
 * @typedef {Array.<TwoDBin>} TwoDBinArray
 */

/**
 * Create a function for binning data in two dimensions.
 *
 * @constructor
 * @param {number[]} xThresholds The boundaries for bins along the x-axis
 * @param {number[]} yThresholds The boundaries for bins along the y-axis
 *
 * @return {BinFunction} The function that bins the data
 */
export function bin2d(xThresholds, yThresholds) {
  let x = (d) => d[0];
  let y = (d) => d[1];

  /**
   * Bin data into two-dimensional cells.
   *
   * @param {object[]} data The data to bin
   * @return {TwoDBinArray}
   */
  function bin(data) {
    if (!(xThresholds.length && yThresholds.length && data.length)) return [];

    const colCount = xThresholds.length - 1;
    const rowCount = yThresholds.length - 1;
    const column = scaleThreshold(xThresholds, range(colCount));
    const row = scaleThreshold(yThresholds, range(rowCount));
    const result = new Array(colCount * rowCount);

    for (let d of data) {
      const j = column(x(d));
      const k = row(y(d));
      const idx = k * colCount + j;

      if (result[idx] === undefined) {
        /** @type {TwoDBin} */
        const bin = [];

        bin.x0 = xThresholds[j];
        bin.x1 = xThresholds[j + 1];
        bin.y0 = yThresholds[k];
        bin.y1 = yThresholds[k + 1];

        result[idx] = bin;
      }

      result[idx].push(d);
    }

    return result.filter((bin) => bin !== undefined);
  }

  bin.x = (value = null) => {
    if (value === null) return x;
    x = value;
    return bin;
  };

  bin.y = (value = null) => {
    if (value === null) return y;
    y = value;
    return bin;
  };

  return bin;
}
