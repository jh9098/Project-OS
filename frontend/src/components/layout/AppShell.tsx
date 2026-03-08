"use client";

import AuthGuard from "@/components/layout/AuthGuard";
import Header from "@/components/layout/Header";
import MobileBottomNav from "@/components/layout/MobileBottomNav";
import Sidebar from "@/components/layout/Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-50 text-slate-900 lg:flex">
        <Sidebar />
        <div className="flex min-h-screen flex-1 flex-col">
          <Header />
          <main className="flex-1 p-5 pb-24 lg:p-8">{children}</main>
          <MobileBottomNav />
        </div>
      </div>
    </AuthGuard>
  );
}
