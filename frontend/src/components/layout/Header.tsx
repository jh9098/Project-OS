"use client";

import Button from "@/components/common/Button";
import { useAuthStore } from "@/stores/auth-store";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4 lg:px-8">
      <div>
        <p className="text-sm font-medium text-slate-400">Project OS Dashboard</p>
        <h2 className="text-lg font-bold text-slate-900">오늘 할 일을 빠르게 정리하세요</h2>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden rounded-xl bg-slate-100 px-3 py-2 text-sm text-slate-700 sm:block">
          {user?.username || "admin"}
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            clearAuth();
            router.replace("/login");
          }}
        >
          로그아웃
        </Button>
      </div>
    </header>
  );
}
