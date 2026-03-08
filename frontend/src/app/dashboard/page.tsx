"use client";

import FocusTaskList from "@/components/dashboard/FocusTaskList";
import BlockedProjectList from "@/components/dashboard/BlockedProjectList";
import SummaryCards from "@/components/dashboard/SummaryCards";
import TodayActionList from "@/components/dashboard/TodayActionList";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import { useDashboardSummary } from "@/hooks/useDashboard";

export default function DashboardPage() {
  const { data, isLoading, isError } = useDashboardSummary();

  return (
    <AppShell>
      <PageHeader
        title="Dashboard"
        description="전체 프로젝트와 오늘의 실행 우선순위를 한눈에 봅니다."
      />

      {isLoading ? <LoadingSpinner /> : null}
      {isError || !data ? <EmptyState title="대시보드를 불러오지 못했습니다." /> : null}

      {data ? (
        <div className="space-y-6">
          <SummaryCards summary={data} />

          <div className="grid gap-6 xl:grid-cols-2">
            <TodayActionList
              projects={[
                ...data.high_priority_projects.filter((item) => item.next_action),
                ...data.recent_projects.filter((item) => item.next_action)
              ].slice(0, 8)}
            />
            <FocusTaskList tasks={data.today_focus_tasks} />
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <BlockedProjectList projects={data.blocked_projects} />
            <div className="card">
              <div className="border-b border-slate-200 p-5">
                <h3 className="text-lg font-bold text-slate-900">최근 업데이트 프로젝트</h3>
              </div>
              <div className="divide-y divide-slate-200">
                {data.recent_projects.length ? (
                  data.recent_projects.map((project) => (
                    <div key={project.id} className="p-5">
                      <p className="font-semibold text-slate-900">{project.name}</p>
                      <p className="mt-1 text-sm text-slate-500">{project.summary}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-5">
                    <EmptyState title="최근 프로젝트가 없습니다." />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
