"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field } from "@/components/ui/Field";
import { Input, Textarea } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { ApiError, api, errorMessage } from "@/lib/api";
import type { Campaign, Overview, WorkRow } from "@/lib/types";

export default function AdminPage() {
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [adminKey, setAdminKey] = useState("");
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState("");

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [campaignsLoading, setCampaignsLoading] = useState(false);
  const [selected, setSelected] = useState<Campaign | null>(null);
  const [listError, setListError] = useState("");

  const [cTitle, setCTitle] = useState("");
  const [cDesc, setCDesc] = useState("");
  const [cDeadline, setCDeadline] = useState("");
  const [cFormats, setCFormats] = useState("jpg,jpeg,png,webp");
  const [cMaxMb, setCMaxMb] = useState("10");
  const [creating, setCreating] = useState(false);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [works, setWorks] = useState<WorkRow[]>([]);
  const [worksLoading, setWorksLoading] = useState(false);
  const [fMedium, setFMedium] = useState("");
  const [fSchool, setFSchool] = useState("");
  const [brief, setBrief] = useState("");
  const [briefBusy, setBriefBusy] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [queryBusy, setQueryBusy] = useState(false);
  const [panelError, setPanelError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .listCampaigns()
      .then((list) => {
        if (cancelled) return;
        setCampaigns(list);
        setAuthed(true);
        setListError("");
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 401) {
          setAuthed(false);
        } else {
          setListError(errorMessage(e));
          setAuthed(true);
        }
      })
      .finally(() => {
        if (!cancelled) setCampaignsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  async function login() {
    setLoginBusy(true);
    setLoginError("");
    try {
      await api.login(adminKey);
      setCampaignsLoading(true);
      setReloadKey((k) => k + 1);
    } catch (e) {
      setLoginError(errorMessage(e));
    } finally {
      setLoginBusy(false);
    }
  }

  async function logout() {
    try {
      await api.logout();
    } finally {
      setAuthed(false);
      setSelected(null);
    }
  }

  async function createCampaign() {
    if (!cTitle.trim()) return;
    setCreating(true);
    setPanelError("");
    try {
      await api.createCampaign({
        title: cTitle.trim(),
        description: cDesc.trim(),
        deadline: cDeadline ? cDeadline : null,
        image_formats: cFormats.trim() || "jpg,jpeg,png,webp",
        max_image_mb: parseFloat(cMaxMb) || 10,
      });
      setCTitle("");
      setCDesc("");
      setCDeadline("");
      setCampaignsLoading(true);
      setReloadKey((k) => k + 1);
    } catch (e) {
      setPanelError(errorMessage(e));
    } finally {
      setCreating(false);
    }
  }

  async function selectCampaign(c: Campaign) {
    setSelected(c);
    setBrief("");
    setAnswer("");
    setPanelError("");
    await Promise.all([loadOverview(c.id), loadWorks(c.id)]);
  }

  async function loadOverview(id: number) {
    try {
      setOverview(await api.overview(id));
    } catch (e) {
      setPanelError(errorMessage(e));
    }
  }

  async function loadWorks(id: number) {
    setWorksLoading(true);
    try {
      setWorks(await api.works(id, fMedium.trim() || undefined, fSchool.trim() || undefined));
    } catch (e) {
      setPanelError(errorMessage(e));
    } finally {
      setWorksLoading(false);
    }
  }

  function exportCsv() {
    if (!selected) return;
    const q = new URLSearchParams();
    if (fMedium.trim()) q.set("medium", fMedium.trim());
    if (fSchool.trim()) q.set("school", fSchool.trim());
    window.open(`/api/v1/admin/campaigns/${selected.id}/export.csv?${q.toString()}`, "_blank");
  }

  async function genBrief() {
    if (!selected) return;
    setBriefBusy(true);
    try {
      setBrief((await api.brief(selected.id)).brief);
    } catch (e) {
      setPanelError(errorMessage(e));
    } finally {
      setBriefBusy(false);
    }
  }

  async function ask() {
    if (!selected || !question.trim()) return;
    setQueryBusy(true);
    try {
      setAnswer((await api.query(selected.id, question.trim())).answer);
    } catch (e) {
      setPanelError(errorMessage(e));
    } finally {
      setQueryBusy(false);
    }
  }

  if (authed === null) {
    return (
      <div className="mx-auto flex max-w-xl items-center justify-center gap-2 px-4 py-24 text-muted">
        <Spinner /> 正在检查登录状态…
      </div>
    );
  }

  if (authed === false) {
    return (
      <div className="mx-auto max-w-sm px-4 py-20">
        <Card>
          <h1 className="mb-1 text-lg font-semibold">管理员登录</h1>
          <p className="mb-4 text-sm text-muted">请输入后台管理员密钥。</p>
          <Field label="管理员密钥">
            <Input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && login()}
              placeholder="输入 ADMIN_KEY"
            />
          </Field>
          {loginError && (
            <div className="mb-4">
              <Alert kind="error">{loginError}</Alert>
            </div>
          )}
          <Button className="w-full" onClick={login} disabled={loginBusy}>
            {loginBusy && <Spinner />}
            {loginBusy ? "登录中…" : "登录"}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold">🎨 投稿助手 · 后台</h1>
        <Button variant="ghost" onClick={logout}>退出登录</Button>
      </header>

      <Card className="mb-5">
        <h2 className="mb-3 text-base font-semibold">创建征集活动</h2>
        <Field label="活动标题" required>
          <Input value={cTitle} onChange={(e) => setCTitle(e.target.value)} placeholder="如：2025 高校美术作品展征集" />
        </Field>
        <Field label="活动说明">
          <Textarea rows={2} value={cDesc} onChange={(e) => setCDesc(e.target.value)} />
        </Field>
        <div className="grid grid-cols-1 gap-x-4 sm:grid-cols-3">
          <Field label="截止时间（可选）">
            <Input type="datetime-local" value={cDeadline} onChange={(e) => setCDeadline(e.target.value)} />
          </Field>
          <Field label="允许图片格式">
            <Input value={cFormats} onChange={(e) => setCFormats(e.target.value)} />
          </Field>
          <Field label="单张上限（MB）">
            <Input type="number" min={1} step={0.5} value={cMaxMb} onChange={(e) => setCMaxMb(e.target.value)} />
          </Field>
        </div>
        <Button onClick={createCampaign} disabled={creating || !cTitle.trim()}>
          {creating && <Spinner />}
          {creating ? "创建中…" : "创建并生成投递链接"}
        </Button>
      </Card>

      {panelError && (
        <div className="mb-5">
          <Alert kind="error">{panelError}</Alert>
        </div>
      )}

      <Card className="mb-5">
        <h2 className="mb-3 text-base font-semibold">活动列表</h2>
        {campaignsLoading ? (
          <div className="flex items-center gap-2 py-4 text-sm text-muted">
            <Spinner /> 加载中…
          </div>
        ) : listError ? (
          <Alert kind="error">{listError}</Alert>
        ) : campaigns.length === 0 ? (
          <p className="py-4 text-sm text-muted">暂无活动，请先创建。</p>
        ) : (
          <ul className="space-y-2">
            {campaigns.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => selectCampaign(c)}
                  className={`w-full rounded-xl border px-4 py-3 text-left transition-colors ${
                    selected?.id === c.id ? "border-primary bg-primary/5" : "border-line hover:border-primary/40"
                  }`}
                >
                  <span className="font-medium">{c.title}</span>
                  <span className="ml-2 text-xs text-muted">#{c.id}</span>
                  <span className="block text-xs text-muted">
                    链接 /s/{c.link_token} · {c.image_formats} · ≤{c.max_image_mb}MB
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {selected && (
        <div className="space-y-5">
          <Card>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-base font-semibold">{selected.title}</h2>
              <a
                className="text-sm text-primary hover:underline"
                href={`/s/${selected.link_token}`}
                target="_blank"
                rel="noreferrer"
              >
                打开投递链接 /s/{selected.link_token} ↗
              </a>
            </div>

            {overview && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat value={overview.applicant_count} label="投稿艺术家" />
                <Stat value={overview.work_count} label="作品总数" />
                <div className="col-span-2 rounded-xl bg-line/30 p-4 sm:col-span-2">
                  <p className="text-xs text-muted">学校分布</p>
                  <Tags data={overview.school_distribution} />
                  <p className="mt-2 text-xs text-muted">画种分布</p>
                  <Tags data={overview.medium_distribution} />
                </div>
              </div>
            )}
          </Card>

          <Card>
            <div className="mb-3 flex flex-wrap items-end gap-2">
              <div className="flex-1">
                <Field label="按画种筛选">
                  <Input value={fMedium} onChange={(e) => setFMedium(e.target.value)} placeholder="如：油画" />
                </Field>
              </div>
              <div className="flex-1">
                <Field label="按院校筛选">
                  <Input value={fSchool} onChange={(e) => setFSchool(e.target.value)} placeholder="如：中央美术学院" />
                </Field>
              </div>
              <Button variant="ghost" onClick={() => loadWorks(selected.id)}>筛选</Button>
              <Button variant="ghost" onClick={exportCsv}>导出 CSV</Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs text-muted">
                    <th className="py-2 pr-3 font-medium">作者</th>
                    <th className="py-2 pr-3 font-medium">作品名</th>
                    <th className="py-2 pr-3 font-medium">尺寸</th>
                    <th className="py-2 pr-3 font-medium">画种</th>
                    <th className="py-2 pr-3 font-medium">院校</th>
                    <th className="py-2 pr-3 font-medium">价格</th>
                    <th className="py-2 font-medium">照片</th>
                  </tr>
                </thead>
                <tbody>
                  {worksLoading ? (
                    <tr>
                      <td colSpan={7} className="py-4 text-muted">加载中…</td>
                    </tr>
                  ) : works.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-4 text-muted">暂无作品</td>
                    </tr>
                  ) : (
                    works.map((w) => (
                      <tr key={w.work_id} className="border-b border-line/60 align-top">
                        <td className="py-2 pr-3">
                          {w.applicant_name}
                          <span className="block text-xs text-muted">{w.applicant_phone}</span>
                        </td>
                        <td className="py-2 pr-3">{w.title}</td>
                        <td className="py-2 pr-3">{w.dimensions}</td>
                        <td className="py-2 pr-3">{w.medium}</td>
                        <td className="py-2 pr-3">{w.school}</td>
                        <td className="py-2 pr-3">{w.price}</td>
                        <td className="py-2">
                          {w.image_path ? (
                            <a className="text-primary hover:underline" href={`/files/${w.image_path}`} target="_blank" rel="noreferrer">
                              查看
                            </a>
                          ) : "—"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold">工作简报</h2>
              <Button onClick={genBrief} disabled={briefBusy}>
                {briefBusy && <Spinner />}
                {briefBusy ? "生成中…" : "生成工作简报"}
              </Button>
            </div>
            {brief ? (
              <pre className="whitespace-pre-wrap rounded-xl bg-line/30 p-4 text-sm">{brief}</pre>
            ) : (
              <p className="text-sm text-muted">点击「生成工作简报」查看四栏目简报。</p>
            )}
          </Card>

          <Card>
            <h2 className="mb-3 text-base font-semibold">智能问答</h2>
            <div className="flex gap-2">
              <Input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && ask()}
                placeholder="如：本次征集有哪些学校投稿？"
              />
              <Button onClick={ask} disabled={queryBusy || !question.trim()}>
                {queryBusy && <Spinner />}
                提问
              </Button>
            </div>
            {answer && (
              <pre className="mt-3 whitespace-pre-wrap rounded-xl bg-line/30 p-4 text-sm">{answer}</pre>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-xl bg-line/30 p-4 text-center">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-muted">{label}</p>
    </div>
  );
}

function Tags({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="text-xs text-muted">暂无</span>;
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {entries.map(([k, v]) => (
        <span key={k} className="rounded-md bg-primary/10 px-2 py-0.5 text-xs text-primary">
          {k} {v}
        </span>
      ))}
    </div>
  );
}
