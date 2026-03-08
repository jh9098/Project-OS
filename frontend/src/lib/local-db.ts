import { DashboardSummary } from "@/types/dashboard";
import { Note, NotePayload } from "@/types/note";
import { Project, ProjectFilters, ProjectPayload } from "@/types/project";
import { Relation, RelationFilters, RelationPayload } from "@/types/relation";
import { Task, TaskFilters, TaskPayload } from "@/types/task";
import { PaginatedResponse } from "@/types/common";
import { User } from "@/types/auth";

type LocalDb = {
  projects: Project[];
  tasks: Task[];
  notes: Note[];
  relations: Relation[];
};

const STORAGE_KEY = "project_os_local_db";

const DEFAULT_USER: User = {
  id: "local-user",
  username: "local-admin",
  role: "owner"
};

function nowIso() {
  return new Date().toISOString();
}

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeText(value?: string | null) {
  return (value || "").trim().toLowerCase();
}

function safeJsonParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function sortByUpdatedAtDesc<T extends { updated_at?: string; created_at?: string }>(items: T[]) {
  return [...items].sort((a, b) => {
    const aDate = new Date(a.updated_at || a.created_at || 0).getTime();
    const bDate = new Date(b.updated_at || b.created_at || 0).getTime();
    return bDate - aDate;
  });
}

function toPaginated<T>(items: T[], page = 1, limit = 50): PaginatedResponse<T> {
  const validPage = Number.isFinite(page) && page > 0 ? page : 1;
  const validLimit = Number.isFinite(limit) && limit > 0 ? limit : 50;
  const start = (validPage - 1) * validLimit;
  return {
    items: items.slice(start, start + validLimit),
    total: items.length,
    page: validPage,
    limit: validLimit
  };
}

function readDb(): LocalDb {
  if (typeof window === "undefined") {
    return { projects: [], tasks: [], notes: [], relations: [] };
  }

  const parsed = safeJsonParse<Partial<LocalDb>>(window.localStorage.getItem(STORAGE_KEY), {});

  return {
    projects: parsed.projects || [],
    tasks: parsed.tasks || [],
    notes: parsed.notes || [],
    relations: parsed.relations || []
  };
}

function writeDb(db: LocalDb) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

function withDb<T>(runner: (db: LocalDb) => T): T {
  const db = readDb();
  const result = runner(db);
  writeDb(db);
  return result;
}

function applyProjectFilters(items: Project[], filters: ProjectFilters) {
  return items.filter((project) => {
    const q = normalizeText(filters.q);
    const isMatchedQ =
      !q ||
      normalizeText(project.name).includes(q) ||
      normalizeText(project.summary).includes(q) ||
      normalizeText(project.description).includes(q);

    const isMatchedStatus = !filters.status || project.status === filters.status;
    const isMatchedType = !filters.project_type || project.project_type === filters.project_type;
    const isMatchedPriority = !filters.priority || project.priority === filters.priority;
    const isMatchedMonetization =
      !filters.monetization_type || project.monetization_type === filters.monetization_type;

    return isMatchedQ && isMatchedStatus && isMatchedType && isMatchedPriority && isMatchedMonetization;
  });
}

function applyTaskFilters(items: Task[], filters: TaskFilters) {
  return items.filter((task) => {
    const byProject = !filters.project_id || task.project_id === filters.project_id;
    const byStatus = !filters.task_status || task.task_status === filters.task_status;
    const byPriority = !filters.priority || task.priority === filters.priority;
    const byToday =
      typeof filters.is_today_focus === "boolean" ? task.is_today_focus === filters.is_today_focus : true;
    return byProject && byStatus && byPriority && byToday;
  });
}

function applyNoteFilters(items: Note[], filters: { project_id?: string; note_type?: string; q?: string }) {
  return items.filter((note) => {
    const byProject = !filters.project_id || note.project_id === filters.project_id;
    const byType = !filters.note_type || note.note_type === filters.note_type;
    const q = normalizeText(filters.q);
    const byQ = !q || normalizeText(note.title).includes(q) || normalizeText(note.content).includes(q);
    return byProject && byType && byQ;
  });
}

function applyRelationFilters(items: Relation[], filters: RelationFilters) {
  return items.filter((relation) => {
    const byProject =
      !filters.project_id ||
      relation.source_project_id === filters.project_id ||
      relation.target_project_id === filters.project_id;
    const byType = !filters.relation_type || relation.relation_type === filters.relation_type;
    return byProject && byType;
  });
}

export const localDbApi = {
  me: () => DEFAULT_USER,

  getDashboardSummary: (): DashboardSummary => {
    const db = readDb();
    const sortedProjects = sortByUpdatedAtDesc(db.projects);
    const todayFocusTasks = sortByUpdatedAtDesc(db.tasks.filter((task) => task.is_today_focus)).slice(0, 8);

    return {
      project_counts: {
        total: db.projects.length,
        developing: db.projects.filter((project) => project.status === "developing").length,
        active: db.projects.filter((project) => project.status === "active").length,
        paused: db.projects.filter((project) => project.status === "paused").length,
        blocked: db.projects.filter((project) => !!normalizeText(project.blocker)).length
      },
      today_focus_tasks: todayFocusTasks,
      recent_projects: sortedProjects.slice(0, 6),
      blocked_projects: sortedProjects.filter((project) => !!normalizeText(project.blocker)).slice(0, 6),
      high_priority_projects: sortedProjects
        .filter((project) => project.priority === "high" || project.priority === "critical")
        .slice(0, 6)
    };
  },

  getProjects: (params: ProjectFilters & { page?: number; limit?: number }) => {
    const db = readDb();
    const filtered = applyProjectFilters(sortByUpdatedAtDesc(db.projects), params);
    return toPaginated(filtered, Number(params.page || 1), Number(params.limit || 50));
  },

  getProject: (projectId: string) => {
    const project = readDb().projects.find((item) => item.id === projectId);
    if (!project) throw new Error("프로젝트를 찾을 수 없습니다.");
    return project;
  },

  createProject: (payload: ProjectPayload) =>
    withDb((db) => {
      const timestamp = nowIso();
      const project: Project = {
        ...payload,
        id: makeId("project"),
        slug: payload.slug || payload.name.toLowerCase().replace(/\s+/g, "-"),
        description: payload.description || null,
        current_focus: payload.current_focus || null,
        next_action: payload.next_action || null,
        blocker: payload.blocker || null,
        frontend_repo_url: payload.frontend_repo_url || null,
        backend_repo_url: payload.backend_repo_url || null,
        deploy_url: payload.deploy_url || null,
        admin_url: payload.admin_url || null,
        local_path: payload.local_path || null,
        docs_url: payload.docs_url || null,
        started_at: payload.started_at || null,
        created_at: timestamp,
        updated_at: timestamp
      };
      db.projects.unshift(project);
      return project;
    }),

  updateProject: (projectId: string, payload: Partial<ProjectPayload>) =>
    withDb((db) => {
      const idx = db.projects.findIndex((item) => item.id === projectId);
      if (idx < 0) throw new Error("프로젝트를 찾을 수 없습니다.");
      const current = db.projects[idx];
      const updated: Project = {
        ...current,
        ...payload,
        slug: payload.slug || current.slug,
        updated_at: nowIso()
      };
      db.projects[idx] = updated;
      return updated;
    }),

  deleteProject: (projectId: string) =>
    withDb((db) => {
      db.projects = db.projects.filter((item) => item.id !== projectId);
      db.tasks = db.tasks.filter((task) => task.project_id !== projectId);
      db.notes = db.notes.filter((note) => note.project_id !== projectId);
      db.relations = db.relations.filter(
        (relation) => relation.source_project_id !== projectId && relation.target_project_id !== projectId
      );
      return { ok: true };
    }),

  getTasks: (params: TaskFilters & { page?: number; limit?: number }) => {
    const db = readDb();
    const filtered = applyTaskFilters(sortByUpdatedAtDesc(db.tasks), params);
    return toPaginated(filtered, Number(params.page || 1), Number(params.limit || 50));
  },

  getTask: (taskId: string) => {
    const task = readDb().tasks.find((item) => item.id === taskId);
    if (!task) throw new Error("작업을 찾을 수 없습니다.");
    return task;
  },

  createTask: (payload: TaskPayload) =>
    withDb((db) => {
      const timestamp = nowIso();
      const task: Task = {
        ...payload,
        id: makeId("task"),
        description: payload.description || null,
        due_date: payload.due_date || null,
        blocker: payload.blocker || null,
        is_today_focus: payload.is_today_focus ?? false,
        created_at: timestamp,
        updated_at: timestamp
      };
      db.tasks.unshift(task);
      return task;
    }),

  updateTask: (taskId: string, payload: Partial<TaskPayload>) =>
    withDb((db) => {
      const idx = db.tasks.findIndex((item) => item.id === taskId);
      if (idx < 0) throw new Error("작업을 찾을 수 없습니다.");
      const updated: Task = {
        ...db.tasks[idx],
        ...payload,
        updated_at: nowIso()
      };
      db.tasks[idx] = updated;
      return updated;
    }),

  deleteTask: (taskId: string) =>
    withDb((db) => {
      db.tasks = db.tasks.filter((item) => item.id !== taskId);
      return { ok: true };
    }),

  getRelations: (params: RelationFilters & { page?: number; limit?: number }) => {
    const db = readDb();
    const projectsById = new Map(db.projects.map((project) => [project.id, project.name]));
    const withNames = db.relations.map((relation) => ({
      ...relation,
      source_project_name: projectsById.get(relation.source_project_id),
      target_project_name: projectsById.get(relation.target_project_id)
    }));
    const filtered = applyRelationFilters(sortByUpdatedAtDesc(withNames), params);
    return toPaginated(filtered, Number(params.page || 1), Number(params.limit || 50));
  },

  createRelation: (payload: RelationPayload) =>
    withDb((db) => {
      const relation: Relation = {
        ...payload,
        id: makeId("relation"),
        description: payload.description || null,
        created_at: nowIso()
      };
      db.relations.unshift(relation);
      return relation;
    }),

  deleteRelation: (relationId: string) =>
    withDb((db) => {
      db.relations = db.relations.filter((item) => item.id !== relationId);
      return { ok: true };
    }),

  getNotes: (params: { project_id?: string; note_type?: string; q?: string; page?: number; limit?: number }) => {
    const db = readDb();
    const filtered = applyNoteFilters(sortByUpdatedAtDesc(db.notes), params);
    return toPaginated(filtered, Number(params.page || 1), Number(params.limit || 50));
  },

  getNote: (noteId: string) => {
    const note = readDb().notes.find((item) => item.id === noteId);
    if (!note) throw new Error("노트를 찾을 수 없습니다.");
    return note;
  },

  createNote: (payload: NotePayload) =>
    withDb((db) => {
      const timestamp = nowIso();
      const note: Note = {
        ...payload,
        id: makeId("note"),
        created_at: timestamp,
        updated_at: timestamp
      };
      db.notes.unshift(note);
      return note;
    }),

  updateNote: (noteId: string, payload: Partial<NotePayload>) =>
    withDb((db) => {
      const idx = db.notes.findIndex((item) => item.id === noteId);
      if (idx < 0) throw new Error("노트를 찾을 수 없습니다.");
      const updated: Note = {
        ...db.notes[idx],
        ...payload,
        updated_at: nowIso()
      };
      db.notes[idx] = updated;
      return updated;
    }),

  deleteNote: (noteId: string) =>
    withDb((db) => {
      db.notes = db.notes.filter((item) => item.id !== noteId);
      return { ok: true };
    })
};
