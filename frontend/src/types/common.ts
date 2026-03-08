export type Priority = "low" | "medium" | "high" | "critical";

export type ProjectType =
  | "web"
  | "app"
  | "program"
  | "automation"
  | "crawler"
  | "content"
  | "internal_tool"
  | "data_pipeline"
  | "experiment";

export type DomainType =
  | "stock"
  | "insurance"
  | "blog"
  | "review"
  | "shorts"
  | "automation"
  | "parenting"
  | "general_info"
  | "other";

export type ProjectStatus =
  | "idea"
  | "planning"
  | "developing"
  | "testing"
  | "active"
  | "automated"
  | "paused"
  | "done"
  | "archived";

export type MonetizationType = "direct" | "indirect" | "experimental" | "internal";

export type TaskStatus = "todo" | "doing" | "waiting" | "done" | "dropped";

export type RelationType =
  | "depends_on"
  | "uses_data_from"
  | "outputs_to"
  | "shares_module_with"
  | "promotes"
  | "feeds"
  | "monetizes_with"
  | "related_to";

export type NoteType = "meeting" | "idea" | "decision" | "issue" | "log";

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
};
