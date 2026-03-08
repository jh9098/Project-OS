"use client";

import { api } from "@/lib/api";
import { RelationFilters } from "@/types/relation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useRelations(filters: RelationFilters = {}) {
  return useQuery({
    queryKey: ["relations", filters],
    queryFn: () => api.getRelations({ ...filters, page: 1, limit: 100 })
  });
}

export function useCreateRelation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createRelation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    }
  });
}

export function useDeleteRelation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteRelation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    }
  });
}
