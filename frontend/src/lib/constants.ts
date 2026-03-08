import {
  DomainType,
  MonetizationType,
  NoteType,
  Priority,
  ProjectStatus,
  ProjectType,
  RelationType,
  TaskStatus
} from "@/types/common";

export const PROJECT_TYPES: ProjectType[] = [
  "web",
  "app",
  "program",
  "automation",
  "crawler",
  "content",
  "internal_tool",
  "data_pipeline",
  "experiment"
];

export const DOMAIN_TYPES: DomainType[] = [
  "stock",
  "insurance",
  "blog",
  "review",
  "shorts",
  "automation",
  "parenting",
  "general_info",
  "other"
];

export const PROJECT_STATUSES: ProjectStatus[] = [
  "idea",
  "planning",
  "developing",
  "testing",
  "active",
  "automated",
  "paused",
  "done",
  "archived"
];

export const PRIORITIES: Priority[] = ["low", "medium", "high", "critical"];

export const MONETIZATION_TYPES: MonetizationType[] = ["direct", "indirect", "experimental", "internal"];

export const TASK_STATUSES: TaskStatus[] = ["todo", "doing", "waiting", "done", "dropped"];

export const RELATION_TYPES: RelationType[] = [
  "depends_on",
  "uses_data_from",
  "outputs_to",
  "shares_module_with",
  "promotes",
  "feeds",
  "monetizes_with",
  "related_to"
];

export const NOTE_TYPES: NoteType[] = ["meeting", "idea", "decision", "issue", "log"];
