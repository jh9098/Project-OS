"use client";

import Button from "@/components/common/Button";
import { RELATION_TYPES } from "@/lib/constants";
import { Project } from "@/types/project";
import { RelationPayload } from "@/types/relation";
import { useState } from "react";

export default function RelationForm({
  projects,
  initialProjectId,
  onSubmit
}: {
  projects: Project[];
  initialProjectId?: string;
  onSubmit: (payload: RelationPayload) => Promise<void>;
}) {
  const [form, setForm] = useState<RelationPayload>({
    source_project_id: initialProjectId || projects[0]?.id || "",
    target_project_id: projects[1]?.id || projects[0]?.id || "",
    relation_type: "related_to",
    description: ""
  });
  const [loading, setLoading] = useState(false);

  function patch<K extends keyof RelationPayload>(key: K, value: RelationPayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(form);
      setForm((prev) => ({ ...prev, description: "" }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card p-5" onSubmit={handleSubmit}>
      <h3 className="mb-4 text-lg font-bold text-slate-900">관계 추가</h3>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">출발 프로젝트</label>
          <select value={form.source_project_id} onChange={(e) => patch("source_project_id", e.target.value)}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">대상 프로젝트</label>
          <select value={form.target_project_id} onChange={(e) => patch("target_project_id", e.target.value)}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">관계 유형</label>
          <select value={form.relation_type} onChange={(e) => patch("relation_type", e.target.value as RelationPayload["relation_type"])}>
            {RELATION_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">설명</label>
          <textarea value={form.description || ""} onChange={(e) => patch("description", e.target.value)} />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button disabled={loading} type="submit">
          {loading ? "추가 중..." : "관계 추가"}
        </Button>
      </div>
    </form>
  );
}
