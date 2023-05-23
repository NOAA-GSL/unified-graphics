/**
 * Represents single series of data with an optional name.
 *
 * @property {string} [name] - The name of the series
 * @property {object[]} data - The actual data.
 */
export default class Series {
  constructor(name, data) {
    if (name) {
      this.name = name;
    }
    this.data = data;
    Object.seal(this);
  }
}
