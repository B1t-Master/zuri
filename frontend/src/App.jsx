import { useState } from "react";
import { useAuth } from "./auth.jsx";

export default function App() {
  const { token, role } = useAuth();

  if (!token) return <AuthGate />;
  if (role === "agent") return <Dashboard />;
  return <ChatWidget />;
}

function AuthGate() {
  const { login, register, anonymous } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ first_name: "", email: "", password: "" });
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <main className="auth">
      <h1>Zuri</h1>
      <form onSubmit={submit}>
        {mode !== "login" && (
          <input
            placeholder="First name"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          />
        )}
        <input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        {error && <p className="error">{error}</p>}
        <button type="submit">{mode === "login" ? "Sign in" : "Create account"}</button>
      </form>
      <button onClick={() => anonymous("Guest")}>Continue as guest</button>
      <button onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Create an account" : "Back to sign in"}
      </button>
    </main>
  );
}

// Full chat widget (SSE streaming) lands in Phase 5.
function ChatWidget() {
  const { logout } = useAuth();
  return (
    <main className="chat">
      <header>
        <h1>Zuri — Kenya Airways Help</h1>
        <button onClick={logout}>Sign out</button>
      </header>
      <section className="chat-body">
        <p>Chat interface coming in Phase 5.</p>
      </section>
    </main>
  );
}

// Full agent dashboard (escalation queue) lands in Phase 5.
function Dashboard() {
  const { logout } = useAuth();
  return (
    <main className="dashboard">
      <header>
        <h1>Agent Dashboard</h1>
        <button onClick={logout}>Sign out</button>
      </header>
      <section>
        <p>Escalation queue coming in Phase 5.</p>
      </section>
    </main>
  );
}