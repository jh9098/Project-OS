export default function EmptyState({
  title,
  description
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="card card-section text-center">
      <div className="mx-auto mb-2 h-12 w-12 rounded-full bg-slate-100" />
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
    </div>
  );
}
