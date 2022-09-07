import { range, scaleThreshold } from "d3";

export function bin2d(xThresholds, yThresholds) {
  let x = (d) => d[0];
  let y = (d) => d[1];

  function bin(data) {
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
