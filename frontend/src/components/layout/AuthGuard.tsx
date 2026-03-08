"use client";

import LoadingSpinner from "@/components/common/LoadingSpinner";
import { useAuthStore } from "@/stores/auth-store";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, hydrated, hydrate } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!hydrated) return;
    if (!token && pathname !== "/login") {
      router.replace("/login");
    }
  }, [hydrated, pathname, router, token]);

  if (!hydrated) {
    return <LoadingSpinner label="인증 상태를 확인하는 중..." />;
  }

  if (!token && pathname !== "/login") {
    return <LoadingSpinner label="로그인 화면으로 이동 중..." />;
  }

  return <>{children}</>;
}
