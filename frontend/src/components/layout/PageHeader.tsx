export default function PageHeader({
  title,
  description,
  action
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="page-title">{title}</h1>
        {description ? <p className="page-description mt-1">{description}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
