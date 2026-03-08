"use client";

import Badge from "@/components/common/Badge";
import Button from "@/components/common/Button";
import { formatDate } from "@/lib/utils";
import { Task } from "@/types/task";

type Props = {
  task: Task;
  onQuickStatusChange?: (task: Task, nextStatus: Task["task_status"]) => void;
  onDelete?: (taskId: string) => void;
};

export default function TaskCard({ task, onQuickStatusChange, onDelete }: Props) {
  const nextStatus =
    task.task_status === "todo"
      ? "doing"
      : task.task_status === "doing"
      ? "waiting"
      : task.task_status === "waiting"
      ? "done"
      : "todo";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="mb-2 flex flex-wrap gap-2">
        <Badge label={task.task_status} tone={task.task_status} />
        <Badge label={task.priority} tone={task.priority} />
        {task.is_today_focus ? <Badge label="today" tone="active" /> : null}
      </div>

      <p className="font-semibold text-slate-900">{task.title}</p>
      {task.description ? <p className="mt-2 text-sm text-slate-500">{task.description}</p> : null}
      <p className="mt-3 text-xs text-slate-400">마감일: {formatDate(task.due_date)}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {onQuickStatusChange ? (
          <Button variant="secondary" onClick={() => onQuickStatusChange(task, nextStatus)}>
            상태 변경
          </Button>
        ) : null}
        {onDelete ? (
          <Button variant="danger" onClick={() => onDelete(task.id)}>
            삭제
          </Button>
        ) : null}
      </div>
    </div>
  );
}
