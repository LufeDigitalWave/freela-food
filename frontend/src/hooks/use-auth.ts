"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AuthResponse, User } from "@/lib/types";

export function useAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        await fetchMe();
      } else {
        setLoading(false);
      }
    };
    void init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post<AuthResponse>("/auth/login", {
      email,
      password,
    });
    localStorage.setItem("access_token", data.access_token);
    await fetchMe();
    router.push("/");
  };

  const register = async (
    email: string,
    password: string,
    role: string = "freelancer"
  ) => {
    await api.post("/auth/register", { email, password, role });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
    router.push("/login");
  };

  return { user, loading, login, register, logout, fetchMe };
}
