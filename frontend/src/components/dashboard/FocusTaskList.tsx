import EmptyState from "@/components/common/EmptyState";
import Badge from "@/components/common/Badge";
import { formatDate } from "@/lib/utils";
import { Task } from "@/types/task";

export default function FocusTaskList({ tasks }: { tasks: Task[] }) {
  if (!tasks.length) {
    return <EmptyState title="오늘 집중 작업이 없습니다." description="작업 생성 시 오늘 집중 체크를 사용하세요." />;
  }

  return (
    <div className="card">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-bold text-slate-900">오늘 집중 작업</h3>
      </div>
      <div className="divide-y divide-slate-200">
        {tasks.map((task) => (
          <div key={task.id} className="p-5">
            <div className="mb-2 flex flex-wrap gap-2">
              <Badge label={task.task_status} tone={task.task_status} />
              <Badge label={task.priority} tone={task.priority} />
            </div>
            <p className="font-semibold text-slate-900">{task.title}</p>
            <p className="mt-1 text-sm text-slate-500">마감일: {formatDate(task.due_date)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
