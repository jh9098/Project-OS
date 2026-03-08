"use client";

import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import NoteForm from "@/components/notes/NoteForm";
import NoteList from "@/components/notes/NoteList";
import { useCreateNote, useDeleteNote, useNotes } from "@/hooks/useNotes";
import { useProjects } from "@/hooks/useProjects";
import { ApiError } from "@/lib/api";

export default function NotesPage() {
  const { data: projectsData, isLoading: projectsLoading, isError: projectsError } = useProjects({});
  const { data: notesData, isLoading: notesLoading, isError: notesError, refetch } = useNotes({});
  const createNote = useCreateNote();
  const deleteNote = useDeleteNote();

  const projects = projectsData?.items || [];
  const notes = notesData?.items || [];
  const hasError = projectsError || notesError;

  return (
    <AppShell>
      <PageHeader title="Notes" description="회의, 아이디어, 결정 사항을 프로젝트와 함께 관리합니다." />

      {projectsLoading || notesLoading ? <LoadingSpinner /> : null}

      {!projectsLoading && !notesLoading && hasError ? <EmptyState title="노트를 불러오지 못했습니다." /> : null}

      {!projectsLoading && !notesLoading && !hasError && !projects.length ? (
        <EmptyState title="아직 프로젝트가 없습니다. 새 프로젝트를 만들어 시작하세요." />
      ) : null}

      {!projectsLoading && !notesLoading && !hasError && projects.length ? (
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

          {notes.length ? (
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
          ) : (
            <EmptyState title="아직 메모가 없습니다." description="상단 입력폼에서 첫 메모를 남겨보세요." />
          )}
        </div>
      ) : null}
    </AppShell>
  );
}
