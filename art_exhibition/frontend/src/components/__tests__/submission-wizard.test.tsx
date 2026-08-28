import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SubmissionWizard } from "@/app/s/[token]/submission-wizard";

const campaign = {
  id: 1,
  title: "测试美术展",
  description: "说明文字",
  deadline: null,
  image_formats: "jpg,png",
  max_image_mb: 10,
  link_token: "tok",
};

function mockCampaignFetch(overrides?: { ok?: boolean; status?: number; json?: unknown }) {
  globalThis.fetch = vi.fn(async () => ({
    ok: overrides?.ok ?? true,
    status: overrides?.status ?? 200,
    json: async () => overrides?.json ?? campaign,
  })) as unknown as typeof fetch;
}

describe("SubmissionWizard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("加载后显示活动标题与第①步", async () => {
    mockCampaignFetch();
    render(<SubmissionWizard token="tok" />);
    expect(await screen.findByText("测试美术展")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("真实姓名")).toBeInTheDocument();
  });

  it("可进入第②步上传简历", async () => {
    mockCampaignFetch();
    render(<SubmissionWizard token="tok" />);
    await screen.findByText("测试美术展");
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText(/个人简历/)).toBeInTheDocument();
  });

  it("活动不存在时显示提示", async () => {
    mockCampaignFetch({ ok: false, status: 404, json: { detail: "活动不存在或链接无效" } });
    render(<SubmissionWizard token="tok" />);
    expect(await screen.findByText("活动不存在或链接无效，请与主办方确认链接。")).toBeInTheDocument();
  });
});
