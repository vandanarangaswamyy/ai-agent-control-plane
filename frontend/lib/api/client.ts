export class ApiError extends Error {
  status: number;
  type: string;
  details: unknown;

  constructor(message: string, status: number, type = "ApiError", details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.type = type;
    this.details = details;
  }
}

function resolveBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function buildUrl(path: string): string {
  const base = resolveBaseUrl().replace(/\/$/, "");
  const resolvedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${resolvedPath}`;
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as {
      error?: { type?: string; message?: string };
    };
    return new ApiError(
      body.error?.message ?? response.statusText,
      response.status,
      body.error?.type ?? "ApiError",
      body,
    );
  } catch {
    return new ApiError(response.statusText || "Request failed", response.status);
  }
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as T;
}

export async function requestText(path: string, init?: RequestInit): Promise<string> {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      Accept: "text/plain",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return await response.text();
}

export async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response);
  }
}

