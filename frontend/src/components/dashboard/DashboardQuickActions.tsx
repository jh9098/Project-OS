import Link from "next/link";

const quickActions = [
  { href: "/projects/new", label: "새 프로젝트" },
  { href: "/projects", label: "프로젝트 보기" },
  { href: "/tasks", label: "작업 보기" },
  { href: "/notes", label: "메모 보기" }
];

export default function DashboardQuickActions() {
  return (
    <section className="card card-section">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-900">빠른 실행</h3>
        <p className="mt-1 text-sm text-slate-500">자주 쓰는 화면으로 바로 이동하세요.</p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            {item.label}
          </Link>
        ))}
      </div>
    </section>
  );
}
