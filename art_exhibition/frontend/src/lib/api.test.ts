import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, errorMessage } from "@/lib/api";

function mockFetch(init: { ok: boolean; status: number; json?: unknown }) {
  globalThis.fetch = vi.fn(async () => ({
    ok: init.ok,
    status: init.status,
    json: async () => init.json ?? {},
  })) as unknown as typeof fetch;
}

describe("api 客户端", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("把后端 detail 归一化为可读错误", async () => {
    mockFetch({ ok: false, status: 400, json: { detail: "姓名不能为空" } });
    await expect(api.login("x")).rejects.toMatchObject({
      message: "姓名不能为空",
      status: 400,
      retryable: false,
    });
  });

  it("5xx 与网络错误标记为可重试", async () => {
    mockFetch({ ok: false, status: 500, json: { detail: "服务器错误" } });
    await expect(api.listCampaigns()).rejects.toMatchObject({ retryable: true });

    globalThis.fetch = vi.fn(async () => {
      throw new Error("network down");
    }) as unknown as typeof fetch;
    await expect(api.listCampaigns()).rejects.toMatchObject({ retryable: true, status: 0 });
  });

  it("errorMessage 提取错误消息", () => {
    expect(errorMessage(new ApiError(500, "服务器错误"))).toBe("服务器错误");
    expect(errorMessage(new Error("boom"))).toBe("boom");
    expect(errorMessage("unknown")).toBe("发生未知错误，请稍后重试");
  });
});
