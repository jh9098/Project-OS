"use client";

import Badge from "@/components/common/Badge";
import Button from "@/components/common/Button";
import { Project } from "@/types/project";
import { Relation } from "@/types/relation";

function findProjectName(projects: Project[], id: string) {
  return projects.find((project) => project.id === id)?.name || id;
}

export default function RelationList({
  relations,
  projects,
  onDelete
}: {
  relations: Relation[];
  projects: Project[];
  onDelete: (relationId: string) => void;
}) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-bold text-slate-900">관계 목록</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-5 py-3">출발</th>
              <th className="px-5 py-3">관계</th>
              <th className="px-5 py-3">대상</th>
              <th className="px-5 py-3">설명</th>
              <th className="px-5 py-3">관리</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {relations.length ? (
              relations.map((relation) => (
                <tr key={relation.id}>
                  <td className="px-5 py-4 font-medium text-slate-900">
                    {findProjectName(projects, relation.source_project_id)}
                  </td>
                  <td className="px-5 py-4">
                    <Badge label={relation.relation_type} tone="planning" />
                  </td>
                  <td className="px-5 py-4 font-medium text-slate-900">
                    {findProjectName(projects, relation.target_project_id)}
                  </td>
                  <td className="px-5 py-4 text-slate-500">{relation.description || "-"}</td>
                  <td className="px-5 py-4">
                    <Button variant="danger" onClick={() => onDelete(relation.id)}>
                      삭제
                    </Button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan={5}>
                  등록된 관계가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
