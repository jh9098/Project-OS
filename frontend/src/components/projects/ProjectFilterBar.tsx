"use client";

import Button from "@/components/common/Button";
import { MONETIZATION_TYPES, PRIORITIES, PROJECT_STATUSES, PROJECT_TYPES } from "@/lib/constants";
import { ProjectFilters } from "@/types/project";
import { useState } from "react";

export default function ProjectFilterBar({
  onChange
}: {
  onChange: (filters: ProjectFilters) => void;
}) {
  const [filters, setFilters] = useState<ProjectFilters>({});

  function update(key: keyof ProjectFilters, value: string) {
    const next = { ...filters, [key]: value || undefined };
    setFilters(next);
    onChange(next);
  }

  return (
    <div className="card mb-6 p-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <input
          placeholder="프로젝트 검색"
          value={filters.q || ""}
          onChange={(e) => update("q", e.target.value)}
        />

        <select value={filters.status || ""} onChange={(e) => update("status", e.target.value)}>
          <option value="">상태 전체</option>
          {PROJECT_STATUSES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select
          value={filters.project_type || ""}
          onChange={(e) => update("project_type", e.target.value)}
        >
          <option value="">유형 전체</option>
          {PROJECT_TYPES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select value={filters.priority || ""} onChange={(e) => update("priority", e.target.value)}>
          <option value="">우선순위 전체</option>
          {PRIORITIES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select
          value={filters.monetization_type || ""}
          onChange={(e) => update("monetization_type", e.target.value)}
        >
          <option value="">수익화 전체</option>
          {MONETIZATION_TYPES.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-3 flex justify-end">
        <Button
          variant="secondary"
          onClick={() => {
            setFilters({});
            onChange({});
          }}
        >
          필터 초기화
        </Button>
      </div>
    </div>
  );
}
