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
