"use client";

import TaskColumn from "@/components/tasks/TaskColumn";
import { Task } from "@/types/task";

export default function TaskBoard({
  tasks,
  onQuickStatusChange,
  onDelete
}: {
  tasks: Task[];
  onQuickStatusChange: (task: Task, nextStatus: Task["task_status"]) => void;
  onDelete: (taskId: string) => void;
}) {
  const groups = {
    todo: tasks.filter((task) => task.task_status === "todo"),
    doing: tasks.filter((task) => task.task_status === "doing"),
    waiting: tasks.filter((task) => task.task_status === "waiting"),
    done: tasks.filter((task) => task.task_status === "done")
  };

  return (
    <div className="grid gap-4 xl:grid-cols-4">
      <TaskColumn title="해야 함" tasks={groups.todo} onDelete={onDelete} onQuickStatusChange={onQuickStatusChange} />
      <TaskColumn title="진행중" tasks={groups.doing} onDelete={onDelete} onQuickStatusChange={onQuickStatusChange} />
      <TaskColumn title="대기" tasks={groups.waiting} onDelete={onDelete} onQuickStatusChange={onQuickStatusChange} />
      <TaskColumn title="완료" tasks={groups.done} onDelete={onDelete} onQuickStatusChange={onQuickStatusChange} />
    </div>
  );
}
