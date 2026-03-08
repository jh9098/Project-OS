import { Project } from "@/types/project";
import { Task } from "@/types/task";

export type DashboardSummary = {
  project_counts: {
    total: number;
    developing: number;
    active: number;
    paused: number;
    blocked: number;
  };
  today_focus_tasks: Task[];
  recent_projects: Project[];
  blocked_projects: Project[];
  high_priority_projects: Project[];
};
