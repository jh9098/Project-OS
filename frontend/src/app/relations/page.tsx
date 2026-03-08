"use client";

import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import RelationForm from "@/components/relations/RelationForm";
import RelationList from "@/components/relations/RelationList";
import RelationMiniGraph from "@/components/relations/RelationMiniGraph";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import EmptyState from "@/components/common/EmptyState";
import { ApiError } from "@/lib/api";
import { useProjects } from "@/hooks/useProjects";
import { useCreateRelation, useDeleteRelation, useRelations } from "@/hooks/useRelations";

export default function RelationsPage() {
  const { data: projectsData, isLoading: projectsLoading } = useProjects({});
  const { data: relationsData, isLoading: relationsLoading, refetch } = useRelations({});
  const createRelation = useCreateRelation();
  const deleteRelation = useDeleteRelation();

  const projects = projectsData?.items || [];
  const relations = relationsData?.items || [];

  return (
    <AppShell>
      <PageHeader title="Relations" description="프로젝트 간 연결 구조를 관리합니다." />

      {projectsLoading || relationsLoading ? <LoadingSpinner /> : null}

      {projects.length ? (
        <div className="space-y-6">
          <RelationForm
            projects={projects}
            onSubmit={async (payload) => {
              try {
                await createRelation.mutateAsync(payload);
                await refetch();
              } catch (error) {
                const message = error instanceof ApiError ? error.message : "관계 추가 중 오류가 발생했습니다.";
                alert(message);
              }
            }}
          />

          <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
            <RelationList
              projects={projects}
              relations={relations}
              onDelete={async (relationId) => {
                if (!confirm("이 관계를 삭제할까요?")) return;
                try {
                  await deleteRelation.mutateAsync(relationId);
                  await refetch();
                } catch (error) {
                  const message = error instanceof ApiError ? error.message : "관계 삭제 중 오류가 발생했습니다.";
                  alert(message);
                }
              }}
            />
            <RelationMiniGraph projects={projects} relations={relations} />
          </div>
        </div>
      ) : (
        <EmptyState title="관계를 만들 프로젝트가 없습니다." description="먼저 프로젝트를 등록하세요." />
      )}
    </AppShell>
  );
}
