"use client";

import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import ProjectForm from "@/components/projects/ProjectForm";
import { ApiError } from "@/lib/api";
import { useCreateProject } from "@/hooks/useProjects";
import { ProjectPayload } from "@/types/project";
import { useRouter } from "next/navigation";

export default function NewProjectPage() {
  const router = useRouter();
  const mutation = useCreateProject();

  async function handleSubmit(payload: ProjectPayload) {
    try {
      const result = await mutation.mutateAsync(payload);
      router.push(`/projects/${result.id}`);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "프로젝트 생성 중 오류가 발생했습니다.";
      alert(message);
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="새 프로젝트"
        description="새 프로젝트를 등록하고 운영 정보를 저장합니다."
      />
      <ProjectForm onSubmit={handleSubmit} submitLabel="프로젝트 생성" />
    </AppShell>
  );
}
