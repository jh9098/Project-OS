"use client";

import { api } from "@/lib/api";
import { NoteFilters } from "@/types/note";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useNotes(filters: NoteFilters = {}) {
  return useQuery({
    queryKey: ["notes", filters],
    queryFn: () => api.getNotes({ ...filters, page: 1, limit: 100 })
  });
}

export function useCreateNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createNote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    }
  });
}

export function useUpdateNote(noteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof api.updateNote>[1]) => api.updateNote(noteId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    }
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteNote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    }
  });
}
