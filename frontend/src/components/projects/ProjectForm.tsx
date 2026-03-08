"use client";

import Button from "@/components/common/Button";
import { DOMAIN_TYPES, MONETIZATION_TYPES, PRIORITIES, PROJECT_STATUSES, PROJECT_TYPES } from "@/lib/constants";
import { Project, ProjectPayload } from "@/types/project";
import { useState } from "react";

type Props = {
  initialValue?: Partial<Project>;
  onSubmit: (payload: ProjectPayload) => Promise<void>;
  submitLabel?: string;
};

export default function ProjectForm({ initialValue, onSubmit, submitLabel = "저장" }: Props) {
  const [form, setForm] = useState<ProjectPayload>({
    name: initialValue?.name || "",
    slug: initialValue?.slug || "",
    summary: initialValue?.summary || "",
    description: initialValue?.description || "",
    project_type: initialValue?.project_type || "web",
    domain_type: initialValue?.domain_type || "other",
    status: initialValue?.status || "planning",
    priority: initialValue?.priority || "medium",
    monetization_type: initialValue?.monetization_type || "internal",
    current_focus: initialValue?.current_focus || "",
    next_action: initialValue?.next_action || "",
    blocker: initialValue?.blocker || "",
    frontend_repo_url: initialValue?.frontend_repo_url || "",
    backend_repo_url: initialValue?.backend_repo_url || "",
    deploy_url: initialValue?.deploy_url || "",
    admin_url: initialValue?.admin_url || "",
    local_path: initialValue?.local_path || "",
    docs_url: initialValue?.docs_url || "",
    started_at: initialValue?.started_at || ""
  });
  const [loading, setLoading] = useState(false);

  function patch<K extends keyof ProjectPayload>(key: K, value: ProjectPayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(form);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="card">
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">프로젝트명 *</label>
            <input value={form.name} onChange={(e) => patch("name", e.target.value)} required />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">한 줄 설명 *</label>
            <input value={form.summary} onChange={(e) => patch("summary", e.target.value)} required />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">slug</label>
            <input value={form.slug || ""} onChange={(e) => patch("slug", e.target.value)} placeholder="비워두면 자동 생성" />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">유형</label>
            <select value={form.project_type} onChange={(e) => patch("project_type", e.target.value as ProjectPayload["project_type"])}>
              {PROJECT_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">도메인</label>
            <select value={form.domain_type} onChange={(e) => patch("domain_type", e.target.value as ProjectPayload["domain_type"])}>
              {DOMAIN_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">상태</label>
            <select value={form.status} onChange={(e) => patch("status", e.target.value as ProjectPayload["status"])}>
              {PROJECT_STATUSES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">우선순위</label>
            <select value={form.priority} onChange={(e) => patch("priority", e.target.value as ProjectPayload["priority"])}>
              {PRIORITIES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">수익화 유형</label>
            <select value={form.monetization_type} onChange={(e) => patch("monetization_type", e.target.value as ProjectPayload["monetization_type"])}>
              {MONETIZATION_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">시작일</label>
            <input type="date" value={form.started_at || ""} onChange={(e) => patch("started_at", e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">상세 설명</label>
            <textarea value={form.description || ""} onChange={(e) => patch("description", e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">현재 집중 내용</label>
            <textarea value={form.current_focus || ""} onChange={(e) => patch("current_focus", e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">다음 액션</label>
            <input value={form.next_action || ""} onChange={(e) => patch("next_action", e.target.value)} />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700">Blocker</label>
            <textarea value={form.blocker || ""} onChange={(e) => patch("blocker", e.target.value)} />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="grid gap-4 p-5 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">Frontend Repo</label>
            <input value={form.frontend_repo_url || ""} onChange={(e) => patch("frontend_repo_url", e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">Backend Repo</label>
            <input value={form.backend_repo_url || ""} onChange={(e) => patch("backend_repo_url", e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">배포 URL</label>
            <input value={form.deploy_url || ""} onChange={(e) => patch("deploy_url", e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">관리 URL</label>
            <input value={form.admin_url || ""} onChange={(e) => patch("admin_url", e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">로컬 경로</label>
            <input value={form.local_path || ""} onChange={(e) => patch("local_path", e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700">문서 URL</label>
            <input value={form.docs_url || ""} onChange={(e) => patch("docs_url", e.target.value)} />
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button disabled={loading} type="submit">
          {loading ? "저장 중..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
