import { requestJson } from "@/lib/api/client";
import type { TraceLookupRead } from "@/lib/api/types";

export async function getTrace(traceId: string): Promise<TraceLookupRead> {
  return requestJson<TraceLookupRead>(`/api/v1/traces/${traceId}`);
}

