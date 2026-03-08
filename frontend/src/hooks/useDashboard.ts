"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: api.getDashboardSummary
  });
}
