import { DashboardSummary } from "@/types/dashboard";

export default function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards = [
    { label: "전체 프로젝트", value: summary.project_counts.total },
    { label: "개발중", value: summary.project_counts.developing },
    { label: "운영중", value: summary.project_counts.active },
    { label: "보류", value: summary.project_counts.paused },
    { label: "Blocker", value: summary.project_counts.blocked }
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => (
        <div key={card.label} className="card card-section">
          <p className="text-sm font-medium text-slate-500">{card.label}</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
