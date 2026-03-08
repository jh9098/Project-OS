import Badge from "@/components/common/Badge";
import { formatDate } from "@/lib/utils";
import { Project } from "@/types/project";
import Link from "next/link";

export default function ProjectCard({ project }: { project: Project }) {
  return (
    <Link href={`/projects/${project.id}`} className="card block p-5 hover:border-slate-300 hover:bg-slate-50">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge label={project.status} tone={project.status} />
        <Badge label={project.priority} tone={project.priority} />
        <Badge label={project.monetization_type} tone={project.monetization_type} />
      </div>

      <h3 className="text-lg font-bold text-slate-900">{project.name}</h3>
      <p className="mt-2 line-clamp-2 text-sm text-slate-500">{project.summary}</p>

      <dl className="mt-5 space-y-2 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-400">유형</dt>
          <dd className="font-medium text-slate-700">{project.project_type}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-400">도메인</dt>
          <dd className="font-medium text-slate-700">{project.domain_type}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-400">최근 수정</dt>
          <dd className="font-medium text-slate-700">{formatDate(project.updated_at)}</dd>
        </div>
      </dl>

      <div className="mt-5 rounded-xl bg-slate-100 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Next Action</p>
        <p className="mt-1 text-sm text-slate-700">{project.next_action || "아직 지정되지 않았습니다."}</p>
      </div>
    </Link>
  );
}
