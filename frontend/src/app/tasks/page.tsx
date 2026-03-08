"use client";

import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import { useProjects } from "@/hooks/useProjects";
import { useCreateTask, useDeleteTask, useTasks } from "@/hooks/useTasks";
import { api, ApiError } from "@/lib/api";
import TaskBoard from "@/components/tasks/TaskBoard";
import TaskForm from "@/components/tasks/TaskForm";

export default function TasksPage() {
  const { data: projectsData, isLoading: projectsLoading, isError: projectsError } = useProjects({});
  const { data: tasksData, isLoading: tasksLoading, isError: tasksError, refetch } = useTasks({});
  const createTask = useCreateTask();
  const deleteTask = useDeleteTask();

  const projects = projectsData?.items || [];
  const tasks = tasksData?.items || [];
  const hasError = projectsError || tasksError;

  return (
    <AppShell>
      <PageHeader
        title="Tasks"
        description="전체 작업을 보드 형태로 관리합니다."
      />

      {projectsLoading || tasksLoading ? <LoadingSpinner /> : null}

      {!projectsLoading && !tasksLoading && hasError ? (
        <EmptyState title="작업 화면을 불러오지 못했습니다." />
      ) : null}

      {!projectsLoading && !tasksLoading && !hasError && !projects.length ? (
        <EmptyState title="아직 프로젝트가 없습니다. 새 프로젝트를 만들어 시작하세요." />
      ) : null}

      {!projectsLoading && !tasksLoading && !hasError && projects.length ? (
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

          {tasks.length ? (
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
          ) : (
            <EmptyState title="아직 작업이 없습니다." description="상단 입력폼에서 첫 작업을 추가해보세요." />
          )}
        </div>
      ) : null}
    </AppShell>
  );
}
