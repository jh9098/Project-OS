import Badge from "@/components/common/Badge";
import { formatDate, formatDateTime } from "@/lib/utils";
import { Project } from "@/types/project";

function LinkRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-slate-200 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
      {value ? (
        value.startsWith("http") ? (
          <a className="break-all text-sm font-medium text-blue-600" href={value} target="_blank" rel="noreferrer">
            {value}
          </a>
        ) : (
          <p className="break-all text-sm font-medium text-slate-700">{value}</p>
        )
      ) : (
        <p className="text-sm text-slate-400">-</p>
      )}
    </div>
  );
}

export default function ProjectOverview({ project }: { project: Project }) {
  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge label={project.status} tone={project.status} />
          <Badge label={project.priority} tone={project.priority} />
          <Badge label={project.monetization_type} tone={project.monetization_type} />
        </div>

        <h2 className="text-2xl font-bold text-slate-900">{project.name}</h2>
        <p className="mt-2 text-slate-600">{project.summary}</p>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <LinkRow label="유형" value={project.project_type} />
          <LinkRow label="도메인" value={project.domain_type} />
          <LinkRow label="시작일" value={formatDate(project.started_at)} />
          <LinkRow label="최근 수정" value={formatDateTime(project.updated_at)} />
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-lg font-bold text-slate-900">운영 정보</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <LinkRow label="현재 집중" value={project.current_focus} />
          <LinkRow label="다음 액션" value={project.next_action} />
          <LinkRow label="Blocker" value={project.blocker} />
          <LinkRow label="설명" value={project.description} />
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-lg font-bold text-slate-900">링크 정보</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <LinkRow label="Frontend Repo" value={project.frontend_repo_url} />
          <LinkRow label="Backend Repo" value={project.backend_repo_url} />
          <LinkRow label="Deploy URL" value={project.deploy_url} />
          <LinkRow label="Admin URL" value={project.admin_url} />
          <LinkRow label="Local Path" value={project.local_path} />
          <LinkRow label="Docs URL" value={project.docs_url} />
        </div>
      </div>
    </div>
  );
}
