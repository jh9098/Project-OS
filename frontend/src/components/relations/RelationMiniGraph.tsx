import Badge from "@/components/common/Badge";
import { Project } from "@/types/project";
import { Relation } from "@/types/relation";

function projectName(projects: Project[], id: string) {
  return projects.find((project) => project.id === id)?.name || id;
}

export default function RelationMiniGraph({
  relations,
  projects,
  focusProjectId
}: {
  relations: Relation[];
  projects: Project[];
  focusProjectId?: string;
}) {
  const filtered = focusProjectId
    ? relations.filter(
        (item) =>
          item.source_project_id === focusProjectId || item.target_project_id === focusProjectId
      )
    : relations;

  return (
    <div className="card p-5">
      <h3 className="text-lg font-bold text-slate-900">간단 연결 맵</h3>
      <div className="mt-4 space-y-3">
        {filtered.length ? (
          filtered.map((relation) => (
            <div
              key={relation.id}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-900">
                  {projectName(projects, relation.source_project_id)}
                </span>
                <Badge label={relation.relation_type} tone="planning" />
                <span className="font-semibold text-slate-900">
                  {projectName(projects, relation.target_project_id)}
                </span>
              </div>
              <p className="text-sm text-slate-500">{relation.description || "설명 없음"}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-400">표시할 관계가 없습니다.</p>
        )}
      </div>
    </div>
  );
}
