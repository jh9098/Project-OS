import { DomainType, MonetizationType, Priority, ProjectStatus, ProjectType } from "@/types/common";

export type Project = {
  id: string;
  name: string;
  slug: string;
  summary: string;
  description?: string | null;
  project_type: ProjectType;
  domain_type: DomainType;
  status: ProjectStatus;
  priority: Priority;
  monetization_type: MonetizationType;
  current_focus?: string | null;
  next_action?: string | null;
  blocker?: string | null;
  frontend_repo_url?: string | null;
  backend_repo_url?: string | null;
  deploy_url?: string | null;
  admin_url?: string | null;
  local_path?: string | null;
  docs_url?: string | null;
  started_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectPayload = {
  name: string;
  slug?: string;
  summary: string;
  description?: string;
  project_type: ProjectType;
  domain_type: DomainType;
  status: ProjectStatus;
  priority: Priority;
  monetization_type: MonetizationType;
  current_focus?: string;
  next_action?: string;
  blocker?: string;
  frontend_repo_url?: string;
  backend_repo_url?: string;
  deploy_url?: string;
  admin_url?: string;
  local_path?: string;
  docs_url?: string;
  started_at?: string;
};

export type ProjectFilters = {
  q?: string;
  status?: string;
  project_type?: string;
  priority?: string;
  monetization_type?: string;
};
