"use client";

import { api } from "@/lib/api";
import { ProjectFilters } from "@/types/project";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useProjects(filters: ProjectFilters = {}) {
  return useQuery({
    queryKey: ["projects", filters],
    queryFn: () => api.getProjects({ ...filters, page: 1, limit: 50 })
  });
}

export function useProject(projectId?: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId as string),
    enabled: !!projectId
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    }
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof api.updateProject>[1]) => api.updateProject(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    }
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    }
  });
}
