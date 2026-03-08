"use client";

import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import NoteForm from "@/components/notes/NoteForm";
import NoteList from "@/components/notes/NoteList";
import { ApiError } from "@/lib/api";
import { useCreateNote, useDeleteNote, useNotes } from "@/hooks/useNotes";
import { useProjects } from "@/hooks/useProjects";

export default function NotesPage() {
  const { data: projectsData, isLoading: projectsLoading } = useProjects({});
  const { data: notesData, isLoading: notesLoading, refetch } = useNotes({});
  const createNote = useCreateNote();
  const deleteNote = useDeleteNote();

  const projects = projectsData?.items || [];
  const notes = notesData?.items || [];

  return (
    <AppShell>
      <PageHeader title="Notes" description="회의, 아이디어, 결정 사항을 프로젝트와 함께 관리합니다." />

      {projectsLoading || notesLoading ? <LoadingSpinner /> : null}

      {projects.length ? (
        <div className="space-y-6">
          <NoteForm
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createNote.mutateAsync(payload);
                await refetch();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "노트 저장 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />

          <NoteList
            notes={notes}
            onDelete={async (noteId) => {
              if (!confirm("이 노트를 삭제할까요?")) return;
              try {
                await deleteNote.mutateAsync(noteId);
                await refetch();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "노트 삭제 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />
        </div>
      ) : (
        <EmptyState title="프로젝트가 없습니다." description="노트를 붙일 프로젝트를 먼저 생성하세요." />
      )}
    </AppShell>
  );
}
