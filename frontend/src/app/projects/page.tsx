"use client";

import Button from "@/components/common/Button";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import ProjectCard from "@/components/projects/ProjectCard";
import ProjectFilterBar from "@/components/projects/ProjectFilterBar";
import { useProjects } from "@/hooks/useProjects";
import { ProjectFilters } from "@/types/project";
import Link from "next/link";
import { useState } from "react";

export default function ProjectsPage() {
  const [filters, setFilters] = useState<ProjectFilters>({});
  const { data, isLoading, isError } = useProjects(filters);

  return (
    <AppShell>
      <PageHeader
        title="Projects"
        description="전체 프로젝트를 탐색하고 상태를 관리합니다."
        action={
          <Link href="/projects/new">
            <Button>새 프로젝트</Button>
          </Link>
        }
      />

      <ProjectFilterBar onChange={setFilters} />

      {isLoading ? <LoadingSpinner /> : null}

      {!isLoading && isError ? <EmptyState title="프로젝트를 불러오지 못했습니다." /> : null}

      {!isLoading && !isError && !data?.items.length ? (
        <EmptyState
          title="아직 프로젝트가 없습니다. 새 프로젝트를 만들어 시작하세요."
          description="상단의 새 프로젝트 버튼으로 바로 시작할 수 있어요."
        />
      ) : null}

      {!isError ? (
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {data?.items.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : null}
    </AppShell>
  );
}
