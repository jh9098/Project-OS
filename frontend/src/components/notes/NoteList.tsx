"use client";

import Badge from "@/components/common/Badge";
import Button from "@/components/common/Button";
import { formatDateTime } from "@/lib/utils";
import { Note } from "@/types/note";

export default function NoteList({
  notes,
  onDelete
}: {
  notes: Note[];
  onDelete: (noteId: string) => void;
}) {
  return (
    <div className="space-y-4">
      {notes.length ? (
        notes.map((note) => (
          <div key={note.id} className="card p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge label={note.note_type} tone={note.note_type === "idea" ? "idea_note" : note.note_type} />
              <span className="text-xs text-slate-400">{formatDateTime(note.created_at)}</span>
            </div>
            <h3 className="text-lg font-bold text-slate-900">{note.title}</h3>
            <p className="mt-2 whitespace-pre-line text-sm text-slate-600">{note.content}</p>

            <div className="mt-4 flex justify-end">
              <Button variant="danger" onClick={() => onDelete(note.id)}>
                삭제
              </Button>
            </div>
          </div>
        ))
      ) : (
        <div className="card p-8 text-center text-sm text-slate-400">등록된 노트가 없습니다.</div>
      )}
    </div>
  );
}
