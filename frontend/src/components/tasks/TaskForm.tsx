"use client";

import Button from "@/components/common/Button";
import { PRIORITIES, TASK_STATUSES } from "@/lib/constants";
import { Project } from "@/types/project";
import { TaskPayload } from "@/types/task";
import { useState } from "react";

type Props = {
  projects: Project[];
  initialProjectId?: string;
  onSubmit: (payload: TaskPayload) => Promise<void>;
};

export default function TaskForm({ projects, initialProjectId, onSubmit }: Props) {
  const [form, setForm] = useState<TaskPayload>({
    project_id: initialProjectId || projects[0]?.id || "",
    title: "",
    description: "",
    task_status: "todo",
    priority: "medium",
    due_date: "",
    is_today_focus: false,
    blocker: ""
  });
  const [loading, setLoading] = useState(false);

  function patch<K extends keyof TaskPayload>(key: K, value: TaskPayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!form.project_id) return;
    setLoading(true);
    try {
      await onSubmit(form);
      setForm({
        project_id: initialProjectId || projects[0]?.id || "",
        title: "",
        description: "",
        task_status: "todo",
        priority: "medium",
        due_date: "",
        is_today_focus: false,
        blocker: ""
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card p-5" onSubmit={handleSubmit}>
      <h3 className="mb-4 text-lg font-bold text-slate-900">작업 추가</h3>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">프로젝트</label>
          <select value={form.project_id} onChange={(e) => patch("project_id", e.target.value)}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">제목</label>
          <input value={form.title} onChange={(e) => patch("title", e.target.value)} required />
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">상태</label>
          <select value={form.task_status} onChange={(e) => patch("task_status", e.target.value as TaskPayload["task_status"])}>
            {TASK_STATUSES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">우선순위</label>
          <select value={form.priority} onChange={(e) => patch("priority", e.target.value as TaskPayload["priority"])}>
            {PRIORITIES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">마감일</label>
          <input type="date" value={form.due_date || ""} onChange={(e) => patch("due_date", e.target.value)} />
        </div>

        <div className="flex items-end">
          <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
            <input
              checked={!!form.is_today_focus}
              onChange={(e) => patch("is_today_focus", e.target.checked)}
              type="checkbox"
            />
            오늘 집중 작업
          </label>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">설명</label>
          <textarea value={form.description || ""} onChange={(e) => patch("description", e.target.value)} />
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">Blocker</label>
          <input value={form.blocker || ""} onChange={(e) => patch("blocker", e.target.value)} />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button disabled={loading} type="submit">
          {loading ? "추가 중..." : "작업 추가"}
        </Button>
      </div>
    </form>
  );
}
