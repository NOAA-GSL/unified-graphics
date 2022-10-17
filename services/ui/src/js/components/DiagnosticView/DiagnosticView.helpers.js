export function containedIn(range, prop) {
  function filter(feature) {
    // If no range is specified, allow all points
    if (!range) return true;

    // If this feature is not a point, exclude it
    if (feature.geometry.type !== "Point") return false;

    const val = feature.properties[prop];

    if (val === undefined) return false;

    const lower = Math.min(...range);
    const upper = Math.max(...range);

    if (lower === upper) return true;

    if (val < lower || val > upper) return false;

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
