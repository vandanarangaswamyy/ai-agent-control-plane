import { requestText } from "@/lib/api/client";

export async function getMetricsText(): Promise<string> {
  return requestText("/metrics");
}

