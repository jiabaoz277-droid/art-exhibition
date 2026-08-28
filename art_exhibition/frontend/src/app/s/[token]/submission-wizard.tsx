"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { ApiError, api, errorMessage } from "@/lib/api";
import type { Campaign, CheckReport } from "@/lib/types";

type WorkDraft = {
  title: string;
  dimensions: string;
  medium: string;
  school: string;
  price: string;
  image: File | null;
};

const STEPS = ["个人资料", "上传简历", "作品资料", "确认提交"];

function emptyWork(): WorkDraft {
  return { title: "", dimensions: "", medium: "", school: "", price: "", image: null };
}

export function SubmissionWizard({ token }: { token: string }) {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [phase, setPhase] = useState<"loading" | "not_found" | "ready" | "error">("loading");
  const [step, setStep] = useState(0);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [wechat, setWechat] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [works, setWorks] = useState<WorkDraft[]>([emptyWork()]);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [report, setReport] = useState<CheckReport | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .getCampaign(token)
      .then((c) => {
        if (cancelled) return;
        setCampaign(c);
        setPhase("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        setPhase(e instanceof ApiError && e.status === 404 ? "not_found" : "error");
      });
    return () => {
      cancelled = true;
    };
  }, [token, reloadKey]);

  const updateWork = (i: number, field: keyof Omit<WorkDraft, "image">, value: string) => {
    setWorks((prev) => prev.map((w, idx) => (idx === i ? { ...w, [field]: value } : w)));
  };
  const setImage = (i: number, file: File | null) => {
    setWorks((prev) => prev.map((w, idx) => (idx === i ? { ...w, image: file } : w)));
  };
  const addWork = () => setWorks((prev) => [...prev, emptyWork()]);
  const removeWork = (i: number) => setWorks((prev) => prev.filter((_, idx) => idx !== i));

  async function handleSubmit() {
    setSubmitting(true);
    setSubmitError("");
    const fd = new FormData();
    fd.append("name", name.trim());
    fd.append("phone", phone.trim());
    fd.append("email", email.trim());
    fd.append("wechat", wechat.trim());
    if (resume) fd.append("resume", resume);
    const meta = works.map((w) => ({
      title: w.title,
      dimensions: w.dimensions,
      medium: w.medium,
      school: w.school,
      price: w.price,
    }));
    fd.append("works_json", JSON.stringify(meta));
    works.forEach((w) => {
      if (w.image) fd.append("images", w.image);
    });
    try {
      const result = await api.submit(token, fd);
      setReport(result.report);
    } catch (e) {
      setSubmitError(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (phase === "loading") {
    return (
      <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 px-4 py-24 text-muted">
        <Spinner /> 正在加载活动…
      </div>
    );
  }
  if (phase === "not_found") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24">
        <Alert kind="error">活动不存在或链接无效，请与主办方确认链接。</Alert>
      </div>
    );
  }
  if (phase === "error") {
    return (
      <div className="mx-auto max-w-2xl px-4 py-24">
        <Alert kind="error">加载失败，请检查网络后重试。</Alert>
        <div className="mt-4">
          <Button
            variant="ghost"
            onClick={() => {
              setPhase("loading");
              setReloadKey((k) => k + 1);
            }}
          >
            重新加载
          </Button>
        </div>
      </div>
    );
  }

  // 提交成功，展示核验报告
  if (report) {
    const pass = report.missing.length === 0 && report.format_issues.length === 0;
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <Card>
          <h2 className="mb-1 text-lg font-semibold">核验报告</h2>
          <p className="mb-4 text-sm text-muted">
            {campaign?.title} · 投稿已提交
          </p>
          {pass && <Alert kind="success">✓ 材料齐全，未发现缺失项或格式问题。</Alert>}
          {report.missing.length > 0 && (
            <div className="mt-4">
              <p className="mb-1 text-sm font-medium text-danger">缺失项</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-danger">
                {report.missing.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            </div>
          )}
          {report.format_issues.length > 0 && (
            <div className="mt-4">
              <p className="mb-1 text-sm font-medium text-warn">格式问题</p>
              <ul className="list-inside list-disc space-y-1 text-sm text-warn">
                {report.format_issues.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          {report.notes && (
            <div className="mt-4 rounded-xl bg-line/30 px-4 py-3 text-sm">{report.notes}</div>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-5">
        <h1 className="text-xl font-semibold">{campaign?.title}</h1>
        {campaign?.description && (
          <p className="mt-1 text-sm text-muted">{campaign.description}</p>
        )}
        <p className="mt-1 text-xs text-muted">
          可上传图片：{campaign?.image_formats}，单张 ≤ {campaign?.max_image_mb}MB
        </p>
      </header>

      <ol className="mb-5 flex gap-2">
        {STEPS.map((s, i) => (
          <li
            key={s}
            className={`flex-1 rounded-lg border px-2 py-2 text-center text-xs ${
              i === step
                ? "border-primary bg-primary text-white"
                : i < step
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-line bg-surface text-muted"
            }`}
          >
            {i + 1}. {s}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <Card>
          <Field label="姓名" required>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="真实姓名" />
          </Field>
          <Field label="电话" required>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="手机号" />
          </Field>
          <Field label="邮箱" hint="邮箱与微信至少填写一项">
            <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="example@mail.com" />
          </Field>
          <Field label="微信">
            <Input value={wechat} onChange={(e) => setWechat(e.target.value)} placeholder="微信号" />
          </Field>
          <div className="mt-2 flex justify-end">
            <Button onClick={() => setStep(1)}>下一步</Button>
          </div>
        </Card>
      )}

      {step === 1 && (
        <Card>
          <Field label="个人简历（PDF / DOCX）" required hint="仅支持 .pdf / .docx，≤ 20MB">
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setResume(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
            />
          </Field>
          <div className="mt-2 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(0)}>上一步</Button>
            <Button onClick={() => setStep(2)}>下一步</Button>
          </div>
        </Card>
      )}

      {step === 2 && (
        <Card>
          {works.map((w, i) => (
            <div key={i} className="mb-5 rounded-xl border border-line p-4">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-semibold">作品 {i + 1}</h3>
                {works.length > 1 && (
                  <button
                    type="button"
                    className="text-xs text-danger hover:underline"
                    onClick={() => removeWork(i)}
                  >
                    删除
                  </button>
                )}
              </div>
              <Field label="作品名" required>
                <Input value={w.title} onChange={(e) => updateWork(i, "title", e.target.value)} />
              </Field>
              <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-2">
                <Field label="尺寸" required>
                  <Input value={w.dimensions} onChange={(e) => updateWork(i, "dimensions", e.target.value)} />
                </Field>
                <Field label="画种" required>
                  <Input value={w.medium} onChange={(e) => updateWork(i, "medium", e.target.value)} />
                </Field>
                <Field label="毕业院校" required>
                  <Input value={w.school} onChange={(e) => updateWork(i, "school", e.target.value)} />
                </Field>
                <Field label="价格">
                  <Input value={w.price} onChange={(e) => updateWork(i, "price", e.target.value)} />
                </Field>
              </div>
              <Field label="作品照片" required>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setImage(i, e.target.files?.[0] ?? null)}
                  className="block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-white"
                />
              </Field>
            </div>
          ))}
          <Button variant="ghost" className="w-full" onClick={addWork}>
            + 添加作品（可多件）
          </Button>
          <div className="mt-4 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(1)}>上一步</Button>
            <Button onClick={() => setStep(3)}>下一步</Button>
          </div>
        </Card>
      )}

      {step === 3 && (
        <Card>
          <h2 className="mb-3 text-base font-semibold">确认提交</h2>
          <dl className="space-y-2 text-sm">
            <div><dt className="inline text-muted">姓名：</dt><dd className="inline">{name || "未填"}</dd></div>
            <div><dt className="inline text-muted">电话：</dt><dd className="inline">{phone || "未填"}</dd></div>
            <div><dt className="inline text-muted">邮箱/微信：</dt><dd className="inline">{email || "—"} / {wechat || "—"}</dd></div>
            <div><dt className="inline text-muted">简历：</dt><dd className="inline">{resume ? resume.name : "未上传"}</dd></div>
            <div><dt className="inline text-muted">作品数：</dt><dd className="inline">{works.length} 件</dd></div>
          </dl>

          {submitError && (
            <div className="mt-4">
              <Alert kind="error">{submitError}</Alert>
            </div>
          )}

          <div className="mt-5 flex justify-between">
            <Button variant="ghost" onClick={() => setStep(2)} disabled={submitting}>上一步</Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting && <Spinner className="h-4 w-4" />}
              {submitting ? "提交中…" : "确认提交"}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
