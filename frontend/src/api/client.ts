import type {
  ActivityCreate,
  ActivityResponse,
  LeadDetailResponse,
  LeadListResponse,
  LeadResponse,
  LeadStatus,
} from "./index";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  error_code?: string;
  request_id?: string;

  constructor(
    message: string,
    status: number,
    error_code?: string,
    request_id?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.error_code = error_code;
    this.request_id = request_id;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail;
    const error_code =
      typeof detail === "object" ? detail?.error_code : undefined;
    throw new ApiError(
      typeof detail === "object" ? detail?.message || response.statusText : String(detail || response.statusText),
      response.status,
      error_code,
      body?.request_id,
    );
  }
  return body as T;
}

export function listLeads(params: {
  status?: LeadStatus | "all";
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<LeadListResponse> {
  const search = new URLSearchParams();
  if (params.status && params.status !== "all") {
    search.set("status", params.status);
  }
  if (params.q) {
    search.set("q", params.q);
  }
  search.set("limit", String(params.limit ?? 50));
  search.set("offset", String(params.offset ?? 0));
  return request(`/api/v1/leads?${search.toString()}`);
}

export function getLead(leadId: string): Promise<LeadDetailResponse> {
  return request(`/api/v1/leads/${leadId}`);
}

export function updateLeadStatus(
  leadId: string,
  status: LeadStatus,
): Promise<LeadResponse> {
  return request(`/api/v1/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function logLeadActivity(
  leadId: string,
  payload: ActivityCreate,
): Promise<ActivityResponse> {
  return request(`/api/v1/leads/${leadId}/activities`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
