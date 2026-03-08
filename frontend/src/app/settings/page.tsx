"use client";

import Button from "@/components/common/Button";
import AppShell from "@/components/layout/AppShell";
import PageHeader from "@/components/layout/PageHeader";
import { useAuthStore } from "@/stores/auth-store";

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return (
    <AppShell>
      <PageHeader title="Settings" description="현재 연결 정보와 로그인 상태를 확인합니다." />

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <h3 className="text-lg font-bold text-slate-900">현재 사용자</h3>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">아이디</dt>
              <dd className="font-medium text-slate-700">{user?.username || "-"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-400">권한</dt>
              <dd className="font-medium text-slate-700">{user?.role || "-"}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-5">
          <h3 className="text-lg font-bold text-slate-900">데이터 저장 방식</h3>
          <p className="mt-4 break-all rounded-xl bg-slate-100 p-4 text-sm text-slate-700">
            브라우저 LocalStorage (오프라인 로컬 모드)
          </p>

          <div className="mt-4">
            <Button variant="danger" onClick={() => clearAuth()}>
              로컬 인증 정보 초기화
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
