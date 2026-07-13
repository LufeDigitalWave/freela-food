import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Interceptor: injeta token do localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor: error handling global
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined") {
      if (error.response?.status === 401) {
        localStorage.removeItem("access_token");
        if (!window.location.pathname.includes("/login")) {
          window.location.href = "/login";
        }
      } else if (error.response?.status >= 500) {
        import("@/components/ui/toast").then(({ showToast }) => {
          showToast("Erro no servidor. Tente novamente.", "error");
        });
      }
    }
    return Promise.reject(error);
  }
);
