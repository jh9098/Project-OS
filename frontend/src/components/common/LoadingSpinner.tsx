export default function LoadingSpinner({ label = "불러오는 중..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-sm text-slate-500">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
      <span>{label}</span>
    </div>
  );
}
