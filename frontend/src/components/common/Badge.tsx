import { cn } from "@/lib/utils";

const toneMap: Record<string, string> = {
  idea: "bg-slate-100 text-slate-700",
  planning: "bg-slate-200 text-slate-700",
  developing: "bg-blue-100 text-blue-700",
  testing: "bg-amber-100 text-amber-700",
  active: "bg-green-100 text-green-700",
  automated: "bg-emerald-100 text-emerald-700",
  paused: "bg-orange-100 text-orange-700",
  done: "bg-neutral-100 text-neutral-700",
  archived: "bg-zinc-100 text-zinc-700",
  low: "bg-slate-100 text-slate-700",
  medium: "bg-sky-100 text-sky-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
  direct: "bg-fuchsia-100 text-fuchsia-700",
  indirect: "bg-indigo-100 text-indigo-700",
  experimental: "bg-cyan-100 text-cyan-700",
  internal: "bg-stone-100 text-stone-700",
  todo: "bg-slate-100 text-slate-700",
  doing: "bg-blue-100 text-blue-700",
  waiting: "bg-amber-100 text-amber-700",
  dropped: "bg-zinc-100 text-zinc-700",
  meeting: "bg-violet-100 text-violet-700",
  idea_note: "bg-sky-100 text-sky-700",
  decision: "bg-green-100 text-green-700",
  issue: "bg-red-100 text-red-700",
  log: "bg-slate-100 text-slate-700"
};

export default function Badge({
  label,
  tone
}: {
  label: string;
  tone?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold capitalize",
        toneMap[tone || ""] || "bg-slate-100 text-slate-700"
      )}
    >
      {label}
    </span>
  );
}
