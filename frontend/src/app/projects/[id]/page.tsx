"use client";

import Button from "@/components/common/Button";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import NoteForm from "@/components/notes/NoteForm";
import NoteList from "@/components/notes/NoteList";
import ProjectOverview from "@/components/projects/ProjectOverview";
import RelationForm from "@/components/relations/RelationForm";
import RelationList from "@/components/relations/RelationList";
import TaskBoard from "@/components/tasks/TaskBoard";
import TaskForm from "@/components/tasks/TaskForm";
import { api, ApiError } from "@/lib/api";
import { useCreateNote, useDeleteNote, useNotes } from "@/hooks/useNotes";
import { useDeleteProject, useProject, useProjects } from "@/hooks/useProjects";
import { useCreateRelation, useDeleteRelation, useRelations } from "@/hooks/useRelations";
import { useCreateTask, useDeleteTask, useTasks } from "@/hooks/useTasks";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

const tabs = [
  { key: "overview", label: "Overview" },
  { key: "tasks", label: "Tasks" },
  { key: "relations", label: "Relations" },
  { key: "notes", label: "Notes" }
] as const;

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const [tab, setTab] = useState<(typeof tabs)[number]["key"]>("overview");

  const { data: project, isLoading: projectLoading } = useProject(projectId);
  const { data: projectsData } = useProjects({});
  const { data: taskData, refetch: refetchTasks } = useTasks({ project_id: projectId });
  const { data: relationData, refetch: refetchRelations } = useRelations({ project_id: projectId });
  const { data: noteData, refetch: refetchNotes } = useNotes({ project_id: projectId });

  const createTask = useCreateTask();
  const deleteTask = useDeleteTask();
  const createRelation = useCreateRelation();
  const deleteRelation = useDeleteRelation();
  const createNote = useCreateNote();
  const deleteNote = useDeleteNote();
  const deleteProject = useDeleteProject();

  const projects = projectsData?.items || [];
  const tasks = taskData?.items || [];
  const relations = relationData?.items || [];
  const notes = noteData?.items || [];

  async function handleDeleteProject() {
    if (!project || !confirm("정말 이 프로젝트를 삭제할까요?")) return;
    try {
      await deleteProject.mutateAsync(project.id);
      router.replace("/projects");
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "삭제 중 오류가 발생했습니다.";
      alert(message);
    }
  }

  if (projectLoading || !project) {
    return (
      <AppShell>
        <LoadingSpinner />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title={project.name}
        description={project.summary}
        action={
          <div className="flex gap-2">
            <Link href={`/projects/${projectId}/edit`}>
              <Button variant="secondary">수정</Button>
            </Link>
            <Button variant="danger" onClick={handleDeleteProject}>
              삭제
            </Button>
          </div>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((item) => (
          <Button
            key={item.key}
            variant={tab === item.key ? "primary" : "secondary"}
            onClick={() => setTab(item.key)}
          >
            {item.label}
          </Button>
        ))}
      </div>

      {tab === "overview" ? <ProjectOverview project={project} /> : null}

      {tab === "tasks" ? (
        <div className="space-y-6">
          <TaskForm
            initialProjectId={projectId}
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createTask.mutateAsync(payload);
                await refetchTasks();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "작업 추가 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />

          {tasks.length ? (
            <TaskBoard
              tasks={tasks}
              onDelete={async (taskId) => {
                if (!confirm("이 작업을 삭제할까요?")) return;
                try {
                  await deleteTask.mutateAsync(taskId);
                  await refetchTasks();
                } catch (error) {
                  const message = error instanceof ApiError ? error.message : "작업 삭제 중 오류가 발생했습니다.";
                  alert(message);
                }
              }}
              onQuickStatusChange={async (task, nextStatus) => {
                try {
                  await api.updateTask(task.id, {
                    task_status: nextStatus,
                    is_today_focus: nextStatus === "done" ? false : task.is_today_focus
                  });
                  await refetchTasks();
                } catch (error) {
                  const message = error instanceof ApiError ? error.message : "상태 변경 중 오류가 발생했습니다.";
                  alert(message);
                }
              }}
            />
          ) : (
            <EmptyState title="이 프로젝트의 작업이 없습니다." />
          )}
        </div>
      ) : null}

      {tab === "relations" ? (
        <div className="space-y-6">
          <RelationForm
            initialProjectId={projectId}
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createRelation.mutateAsync(payload);
                await refetchRelations();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "관계 추가 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />

          <RelationList
            projects={projects}
            relations={relations}
            onDelete={async (relationId) => {
              if (!confirm("이 관계를 삭제할까요?")) return;
              try {
                await deleteRelation.mutateAsync(relationId);
                await refetchRelations();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "관계 삭제 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />
        </div>
      ) : null}

      {tab === "notes" ? (
        <div className="space-y-6">
          <NoteForm
            initialProjectId={projectId}
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createNote.mutateAsync(payload);
                await refetchNotes();
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
                await refetchNotes();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "노트 삭제 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />
        </div>
      ) : null}
    </AppShell>
  );
}
