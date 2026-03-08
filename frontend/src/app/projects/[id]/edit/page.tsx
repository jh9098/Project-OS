"use client";

import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import ProjectForm from "@/components/projects/ProjectForm";
import { ApiError } from "@/lib/api";
import { useProject, useUpdateProject } from "@/hooks/useProjects";
import { ProjectPayload } from "@/types/project";
import { useParams, useRouter } from "next/navigation";

export default function EditProjectPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const { data, isLoading } = useProject(projectId);
  const mutation = useUpdateProject(projectId);

  async function handleSubmit(payload: ProjectPayload) {
    try {
      await mutation.mutateAsync(payload);
      router.push(`/projects/${projectId}`);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "프로젝트 수정 중 오류가 발생했습니다.";
      alert(message);
    }
  }

  return (
    <AppShell>
      <PageHeader title="프로젝트 수정" description="프로젝트 정보를 수정합니다." />
      {isLoading || !data ? <LoadingSpinner /> : <ProjectForm initialValue={data} onSubmit={handleSubmit} submitLabel="변경 저장" />}
    </AppShell>
  );
}
