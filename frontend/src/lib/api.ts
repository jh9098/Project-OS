import { DashboardSummary } from "@/types/dashboard";
import { Note, NotePayload } from "@/types/note";
import { Project, ProjectPayload } from "@/types/project";
import { Relation, RelationPayload } from "@/types/relation";
import { Task, TaskPayload } from "@/types/task";
import { PaginatedResponse } from "@/types/common";
import { localDbApi } from "@/lib/local-db";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("project_os_token");
}

async function localRequest<T>(action: () => T): Promise<T> {
  try {
    return action();
  } catch (error) {
    const message = error instanceof Error ? error.message : "로컬 데이터 처리 중 오류가 발생했습니다.";
    throw new ApiError(message, 400);
  }
}

export const api = {
  me: () => localRequest(() => localDbApi.me()),

  getDashboardSummary: () => localRequest<DashboardSummary>(() => localDbApi.getDashboardSummary()),

  getProjects: (params: Record<string, string | number | boolean | undefined>) =>
    localRequest<PaginatedResponse<Project>>(() =>
      localDbApi.getProjects({
        ...params,
        page: Number(params.page || 1),
        limit: Number(params.limit || 50)
      })
    ),

  getProject: (projectId: string) => localRequest<Project>(() => localDbApi.getProject(projectId)),

  createProject: (payload: ProjectPayload) => localRequest<Project>(() => localDbApi.createProject(payload)),

  updateProject: (projectId: string, payload: Partial<ProjectPayload>) =>
    localRequest<Project>(() => localDbApi.updateProject(projectId, payload)),

  deleteProject: (projectId: string) => localRequest<{ ok: boolean }>(() => localDbApi.deleteProject(projectId)),

  getTasks: (params: Record<string, string | number | boolean | undefined>) =>
    localRequest<PaginatedResponse<Task>>(() =>
      localDbApi.getTasks({
        ...params,
        page: Number(params.page || 1),
        limit: Number(params.limit || 100)
      })
    ),

  getTask: (taskId: string) => localRequest<Task>(() => localDbApi.getTask(taskId)),

  createTask: (payload: TaskPayload) => localRequest<Task>(() => localDbApi.createTask(payload)),

  updateTask: (taskId: string, payload: Partial<TaskPayload>) =>
    localRequest<Task>(() => localDbApi.updateTask(taskId, payload)),

  deleteTask: (taskId: string) => localRequest<{ ok: boolean }>(() => localDbApi.deleteTask(taskId)),

  getRelations: (params: Record<string, string | number | boolean | undefined>) =>
    localRequest<PaginatedResponse<Relation>>(() =>
      localDbApi.getRelations({
        ...params,
        page: Number(params.page || 1),
        limit: Number(params.limit || 100)
      })
    ),

  createRelation: (payload: RelationPayload) => localRequest<Relation>(() => localDbApi.createRelation(payload)),

  deleteRelation: (relationId: string) =>
    localRequest<{ ok: boolean }>(() => localDbApi.deleteRelation(relationId)),

  getNotes: (params: Record<string, string | number | boolean | undefined>) =>
    localRequest<PaginatedResponse<Note>>(() =>
      localDbApi.getNotes({
        ...params,
        page: Number(params.page || 1),
        limit: Number(params.limit || 100)
      })
    ),

  getNote: (noteId: string) => localRequest<Note>(() => localDbApi.getNote(noteId)),

  createNote: (payload: NotePayload) => localRequest<Note>(() => localDbApi.createNote(payload)),

  updateNote: (noteId: string, payload: Partial<NotePayload>) =>
    localRequest<Note>(() => localDbApi.updateNote(noteId, payload)),

  deleteNote: (noteId: string) => localRequest<{ ok: boolean }>(() => localDbApi.deleteNote(noteId))
};

export const apiRequest = localRequest;
