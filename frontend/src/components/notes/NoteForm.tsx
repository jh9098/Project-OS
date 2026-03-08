"use client";

import Button from "@/components/common/Button";
import { NOTE_TYPES } from "@/lib/constants";
import { NotePayload } from "@/types/note";
import { Project } from "@/types/project";
import { useState } from "react";

export default function NoteForm({
  projects,
  initialProjectId,
  onSubmit
}: {
  projects: Project[];
  initialProjectId?: string;
  onSubmit: (payload: NotePayload) => Promise<void>;
}) {
  const [form, setForm] = useState<NotePayload>({
    project_id: initialProjectId || projects[0]?.id || "",
    note_type: "meeting",
    title: "",
    content: ""
  });
  const [loading, setLoading] = useState(false);

  function patch<K extends keyof NotePayload>(key: K, value: NotePayload[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(form);
      setForm((prev) => ({ ...prev, title: "", content: "" }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="card p-5" onSubmit={handleSubmit}>
      <h3 className="mb-4 text-lg font-bold text-slate-900">노트 추가</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">프로젝트</label>
          <select value={form.project_id} onChange={(e) => patch("project_id", e.target.value)}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">노트 유형</label>
          <select value={form.note_type} onChange={(e) => patch("note_type", e.target.value as NotePayload["note_type"])}>
            {NOTE_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">제목</label>
          <input value={form.title} onChange={(e) => patch("title", e.target.value)} required />
        </div>

        <div className="md:col-span-2">
          <label className="mb-1 block text-sm font-semibold text-slate-700">내용</label>
          <textarea value={form.content} onChange={(e) => patch("content", e.target.value)} required />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button disabled={loading} type="submit">
          {loading ? "저장 중..." : "노트 저장"}
        </Button>
      </div>
    </form>
  );
}
