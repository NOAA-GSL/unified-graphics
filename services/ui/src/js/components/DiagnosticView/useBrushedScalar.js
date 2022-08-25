import { useCallback, useState } from "preact/hooks";

export default function useBrushedScalar({ features = [], loop = "", variable = "" }) {
  const [selection, setSelection] = useState(null);

  const setBrush = useCallback((selection) => setSelection(selection), []);

  let brushedScalar = features
    .filter((feature) => {
      if (selection === null) return true;

      const [[left, top], [right, bottom]] = selection;
      const [lng, lat] = feature.geometry.coordinates;

      return lng >= left && lng <= right && lat >= bottom && lat <= top;
    })
    .map((feature) => feature.properties[loop][variable]);

  return [brushedScalar, setBrush];
}
