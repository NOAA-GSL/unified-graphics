export function containedIn(range, loop) {
  function filter(feature) {
    // If no range is specified, allow all points
    if (!range) return true;

    // If this feature is not a point, exclude it
    if (feature.geometry.type !== "Point") return false;

    // If range is an array, then we're dealing with a scalar variable.
    // Otherwise, we're filtering on multiple dimensions and need to test each
    // point to ensure it falls within the range of every dimensions.
    if (Array.isArray(range)) {
      const val = feature.properties[loop];

      const lower = Math.min(...range);
      const upper = Math.max(...range);

      // Include this point if the range is effectively 0
      if (lower === upper) return true;

      // Exclude the point if it doesn't have a value for loop, or if it falls
      // outside the range
      if (val === undefined || val < lower || val > upper) return false;
    } else {
      // Range is not an array, so need to iterate over the properties in the
      // object and check our point for each property.
      for (let [name, [lower, upper]] of Object.entries(range)) {
        const val = feature.properties[loop][name];

        // If the range for this dimension is 0, we won't reject the point
        // based this dimension.
        if (lower === upper) continue;

        // Exlcude this point if it doesn't have this dimension, or if its
        // value falls outside of the range.
        if (val === undefined || val < lower || val > upper) return false;
      }
    }

    // If we've made it this far, we can include this point.
    return true;
  }

  return filter;
}

export function geoFilter(bbox) {
  function filter(feature) {
    // If this feature is not a point, exclude it
    if (feature.geometry.type !== "Point") return false;

    // If no bounding box is specified, include all points
    if (!bbox) return true;

    const [[left, top], [right, bottom]] = bbox;
    const [x, y] = feature.geometry.coordinates;

    return x >= left && x <= right && y >= bottom && y <= top;
  }

  return filter;
}

export function calculateMagnitude(feature) {
  const u = feature.properties.adjusted.u;
  const v = feature.properties.adjusted.v;
  return Math.sqrt(u * u + v * v);
}
