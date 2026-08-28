import type {
  BriefResult,
  Campaign,
  Overview,
  QueryResult,
  SubmissionResult,
  WorkRow,
} from "./types";

export class ApiError extends Error {
  status: number;
  retryable: boolean;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryable = status >= 500 || status === 0;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { credentials: "include", ...init });
  } catch {
    throw new ApiError(0, "网络连接失败，请检查网络后重试");
  }
  if (!res.ok) {
    let message = `请求失败（${res.status}）`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") message = body.detail;
    } catch {
      /* 忽略非 JSON 错误体 */
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getCampaign: (token: string) => request<Campaign>(`/api/v1/campaigns/${token}`),

  submit: (token: string, form: FormData) =>
    request<SubmissionResult>(`/api/v1/campaigns/${token}/submissions`, {
      method: "POST",
      body: form, // FormData：不设置 Content-Type，浏览器自动带 boundary
    }),

  login: (adminKey: string) =>
    request<{ ok: boolean }>("/api/v1/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ admin_key: adminKey }),
    }),

  logout: () =>
    request<{ ok: boolean }>("/api/v1/admin/logout", { method: "POST" }),

  listCampaigns: () => request<Campaign[]>("/api/v1/admin/campaigns"),

  createCampaign: (body: {
    title: string;
    description: string;
    deadline: string | null;
    image_formats: string;
    max_image_mb: number;
  }) =>
    request<Campaign>("/api/v1/admin/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  overview: (id: number) => request<Overview>(`/api/v1/admin/campaigns/${id}/overview`),

  works: (id: number, medium?: string, school?: string) => {
    const q = new URLSearchParams();
    if (medium) q.set("medium", medium);
    if (school) q.set("school", school);
    return request<WorkRow[]>(`/api/v1/admin/campaigns/${id}/works?${q.toString()}`);
  },

  brief: (id: number) =>
    request<BriefResult>(`/api/v1/admin/campaigns/${id}/brief`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }),

  query: (id: number, question: string) =>
    request<QueryResult>(`/api/v1/admin/campaigns/${id}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "发生未知错误，请稍后重试";
}
