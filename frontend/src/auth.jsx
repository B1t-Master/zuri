import { createContext, useContext, useState } from "react";
import { api } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("zuri_token"));
  const [role, setRole] = useState(() => localStorage.getItem("zuri_role"));

  const persist = (t, r) => {
    localStorage.setItem("zuri_token", t);
    localStorage.setItem("zuri_role", r);
    setToken(t);
    setRole(r);
  };

  const login = async (email, password) => {
    const res = await api.login({ email, password });
    persist(res.access_token, res.role);
  };

  const register = async (data) => {
    await api.register(data);
    await login(data.email, data.password);
  };

  const anonymous = async (firstName) => {
    const res = await api.anonymous({ first_name: firstName });
    persist(res.access_token, res.role);
  };

  const logout = () => {
    localStorage.removeItem("zuri_token");
    localStorage.removeItem("zuri_role");
    setToken(null);
    setRole(null);
  };

  return (
    <AuthContext.Provider value={{ token, role, login, register, anonymous, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}