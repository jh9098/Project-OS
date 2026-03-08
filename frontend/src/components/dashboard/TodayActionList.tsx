import EmptyState from "@/components/common/EmptyState";
import Badge from "@/components/common/Badge";
import { Project } from "@/types/project";
import Link from "next/link";

export default function TodayActionList({ projects }: { projects: Project[] }) {
  if (!projects.length) {
    return <EmptyState title="다음 액션이 없습니다." description="next_action이 있는 프로젝트가 여기에 표시됩니다." />;
  }

  return (
    <div className="card">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-bold text-slate-900">오늘의 다음 액션</h3>
      </div>
      <div className="divide-y divide-slate-200">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="block p-5 hover:bg-slate-50"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h4 className="font-semibold text-slate-900">{project.name}</h4>
              <Badge label={project.status} tone={project.status} />
              <Badge label={project.priority} tone={project.priority} />
            </div>
            <p className="text-sm text-slate-600">{project.next_action || "다음 액션이 아직 없습니다."}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
