"use client";

import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import TaskBoard from "@/components/tasks/TaskBoard";
import TaskForm from "@/components/tasks/TaskForm";
import { api, ApiError } from "@/lib/api";
import { useProjects } from "@/hooks/useProjects";
import { useCreateTask, useDeleteTask, useTasks } from "@/hooks/useTasks";

export default function TasksPage() {
  const { data: projectsData, isLoading: projectsLoading } = useProjects({});
  const { data: tasksData, isLoading: tasksLoading, refetch } = useTasks({});
  const createTask = useCreateTask();
  const deleteTask = useDeleteTask();

  const projects = projectsData?.items || [];
  const tasks = tasksData?.items || [];

  return (
    <AppShell>
      <PageHeader
        title="Tasks"
        description="전체 작업을 보드 형태로 관리합니다."
      />

      {projectsLoading || tasksLoading ? <LoadingSpinner /> : null}

      {projects.length ? (
        <div className="space-y-6">
          <TaskForm
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createTask.mutateAsync(payload);
                await refetch();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "작업 추가 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />

          <TaskBoard
            tasks={tasks}
            onDelete={async (taskId) => {
              if (!confirm("이 작업을 삭제할까요?")) return;
              try {
                await deleteTask.mutateAsync(taskId);
                await refetch();
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
                await refetch();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "상태 변경 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />
        </div>
      ) : (
        <EmptyState title="프로젝트가 없습니다." description="먼저 프로젝트를 만들어야 작업을 추가할 수 있습니다." />
      )}
    </AppShell>
  );
}
