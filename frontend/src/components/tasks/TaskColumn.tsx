import TaskCard from "@/components/tasks/TaskCard";
import { Task } from "@/types/task";

export default function TaskColumn({
  title,
  tasks,
  onQuickStatusChange,
  onDelete
}: {
  title: string;
  tasks: Task[];
  onQuickStatusChange: (task: Task, nextStatus: Task["task_status"]) => void;
  onDelete: (taskId: string) => void;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <h3 className="mb-4 text-base font-bold text-slate-900">{title}</h3>
      <div className="space-y-3">
        {tasks.length ? (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onDelete={onDelete}
              onQuickStatusChange={onQuickStatusChange}
            />
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-5 text-center text-sm text-slate-400">
            항목 없음
          </div>
        )}
      </div>
    </div>
  );
}
