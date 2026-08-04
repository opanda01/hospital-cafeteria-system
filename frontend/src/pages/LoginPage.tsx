import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/client";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@demo.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const data = await login(email, password);
      localStorage.setItem("token", data.access_token);
      navigate("/");
    } catch {
      setError("E-posta veya şifre hatalı");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={onSubmit} className="w-full max-w-md bg-white shadow rounded-lg p-6 space-y-4">
        <h1 className="text-xl font-semibold">Yemekhane Yönetim Paneli</h1>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <input
          className="w-full border rounded px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="E-posta"
        />
        <input
          type="password"
          className="w-full border rounded px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Şifre"
        />
        <button type="submit" className="w-full bg-slate-900 text-white rounded py-2">
          Giriş
        </button>
      </form>
    </div>
  );
}
