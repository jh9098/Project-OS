import { RelationType } from "@/types/common";

export type Relation = {
  id: string;
  source_project_id: string;
  target_project_id: string;
  relation_type: RelationType;
  description?: string | null;
  created_at: string;
  source_project_name?: string;
  target_project_name?: string;
};

export type RelationPayload = {
  source_project_id: string;
  target_project_id: string;
  relation_type: RelationType;
  description?: string;
};

export type RelationFilters = {
  project_id?: string;
  relation_type?: string;
};
