export interface PrometheusSnapshot {
  counters: Record<string, number>;
  histograms: Record<string, { sum: number; count: number }>;
}

export function parsePrometheusMetrics(text: string): PrometheusSnapshot {
  const counters: Record<string, number> = {};
  const histograms: Record<string, { sum: number; count: number }> = {};

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const [name, valueText] = line.split(/\s+/, 2);
    if (!name || !valueText) {
      continue;
    }

    const value = Number(valueText);
    if (Number.isNaN(value)) {
      continue;
    }

    if (name.endsWith("_sum")) {
      const baseName = name.slice(0, -4);
      histograms[baseName] = {
        sum: value,
        count: histograms[baseName]?.count ?? 0,
      };
      continue;
    }

    if (name.endsWith("_count")) {
      const baseName = name.slice(0, -6);
      histograms[baseName] = {
        sum: histograms[baseName]?.sum ?? 0,
        count: value,
      };
      continue;
    }

    counters[name] = value;
  }

  return { counters, histograms };
}

export function averageFromHistogram(
  snapshot: PrometheusSnapshot,
  metricName: string,
): number | null {
  const histogram = snapshot.histograms[metricName];
  if (!histogram || histogram.count === 0) {
    return null;
  }

  return histogram.sum / histogram.count;
}

