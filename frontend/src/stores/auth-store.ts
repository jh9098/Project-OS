"use client";

import { User } from "@/types/auth";
import { create } from "zustand";

type AuthState = {
  token: string | null;
  user: User | null;
  hydrated: boolean;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  hydrate: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  hydrated: false,
  setAuth: (token, user) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("project_os_token", token);
      window.localStorage.setItem("project_os_user", JSON.stringify(user));
    }
    set({ token, user, hydrated: true });
  },
  clearAuth: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("project_os_token");
      window.localStorage.removeItem("project_os_user");
    }
    set({ token: null, user: null, hydrated: true });
  },
  hydrate: () => {
    if (typeof window === "undefined") {
      set({ hydrated: true });
      return;
    }
    const token = window.localStorage.getItem("project_os_token");
    const rawUser = window.localStorage.getItem("project_os_user");
    let user: User | null = null;
    if (rawUser) {
      try {
        user = JSON.parse(rawUser);
      } catch {
        user = null;
      }
    }
    set({ token, user, hydrated: true });
  }
}));
