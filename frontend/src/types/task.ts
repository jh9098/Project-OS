import { Priority, TaskStatus } from "@/types/common";

export type Task = {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  task_status: TaskStatus;
  priority: Priority;
  due_date?: string | null;
  is_today_focus: boolean;
  blocker?: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskPayload = {
  project_id: string;
  title: string;
  description?: string;
  task_status: TaskStatus;
  priority: Priority;
  due_date?: string;
  is_today_focus?: boolean;
  blocker?: string;
};

export type TaskFilters = {
  project_id?: string;
  task_status?: string;
  priority?: string;
  is_today_focus?: boolean;
};
