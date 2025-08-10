import * as React from "react";

const DEFAULT_COLORS = [
  "#4F46E5",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#3B82F6",
  "#8B5CF6",
  "#14B8A6",
  "#F97316",
  "#22C55E",
  "#E11D48",
];

export function useColorScale(
  keys: string[],
  palette: string[] = DEFAULT_COLORS
) {
  // Stable mapping: key -> color
  return React.useMemo(() => {
    const map: Record<string, string> = {};
    keys.forEach((k, i) => (map[k] = palette[i % palette.length]));
    return map;
  }, [keys, palette]);
}
