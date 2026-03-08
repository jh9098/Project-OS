import { LoginResponse } from "@/types/auth";
import { DashboardSummary } from "@/types/dashboard";
import { Note, NotePayload } from "@/types/note";
import { Project, ProjectPayload } from "@/types/project";
import { Relation, RelationPayload } from "@/types/relation";
import { Task, TaskPayload } from "@/types/task";
import { PaginatedResponse } from "@/types/common";
import { toQueryString } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

type RequestOptions = RequestInit & {
  auth?: boolean;
};

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

async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const token = getToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(auth && token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers
    }
  });

  if (!response.ok) {
    let message = "요청 처리 중 오류가 발생했습니다.";
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      //
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ username, password })
    }),

  me: () => apiRequest("/auth/me"),

  getDashboardSummary: () => apiRequest<DashboardSummary>("/dashboard/summary"),

  getProjects: (params: Record<string, string | number | boolean | undefined>) =>
    apiRequest<PaginatedResponse<Project>>(`/projects${toQueryString(params)}`),

  getProject: (projectId: string) => apiRequest<Project>(`/projects/${projectId}`),

  createProject: (payload: ProjectPayload) =>
    apiRequest<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  updateProject: (projectId: string, payload: Partial<ProjectPayload>) =>
    apiRequest<Project>(`/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),

  deleteProject: (projectId: string) =>
    apiRequest<{ ok: boolean }>(`/projects/${projectId}`, { method: "DELETE" }),

  getTasks: (params: Record<string, string | number | boolean | undefined>) =>
    apiRequest<PaginatedResponse<Task>>(`/tasks${toQueryString(params)}`),

  getTask: (taskId: string) => apiRequest<Task>(`/tasks/${taskId}`),

  createTask: (payload: TaskPayload) =>
    apiRequest<Task>("/tasks", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  updateTask: (taskId: string, payload: Partial<TaskPayload>) =>
    apiRequest<Task>(`/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),

  deleteTask: (taskId: string) =>
    apiRequest<{ ok: boolean }>(`/tasks/${taskId}`, { method: "DELETE" }),

  getRelations: (params: Record<string, string | number | boolean | undefined>) =>
    apiRequest<PaginatedResponse<Relation>>(`/relations${toQueryString(params)}`),

  createRelation: (payload: RelationPayload) =>
    apiRequest<Relation>("/relations", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  deleteRelation: (relationId: string) =>
    apiRequest<{ ok: boolean }>(`/relations/${relationId}`, { method: "DELETE" }),

  getNotes: (params: Record<string, string | number | boolean | undefined>) =>
    apiRequest<PaginatedResponse<Note>>(`/notes${toQueryString(params)}`),

  getNote: (noteId: string) => apiRequest<Note>(`/notes/${noteId}`),

  createNote: (payload: NotePayload) =>
    apiRequest<Note>("/notes", {
      method: "POST",
      body: JSON.stringify(payload)
    }),

  updateNote: (noteId: string, payload: Partial<NotePayload>) =>
    apiRequest<Note>(`/notes/${noteId}`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    }),

  deleteNote: (noteId: string) =>
    apiRequest<{ ok: boolean }>(`/notes/${noteId}`, { method: "DELETE" })
};

export { apiRequest };
