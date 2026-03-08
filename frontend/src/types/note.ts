import { NoteType } from "@/types/common";

export type Note = {
  id: string;
  project_id: string;
  note_type: NoteType;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
};

export type NotePayload = {
  project_id: string;
  note_type: NoteType;
  title: string;
  content: string;
};

export type NoteFilters = {
  project_id?: string;
  note_type?: string;
  q?: string;
};
