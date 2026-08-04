const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type TokenResponse = { access_token: string; token_type: string };
export type Device = {
  id: number;
  device_key: string;
  konum: string;
  durum: string;
  son_iletisim: string | null;
  online: boolean;
};
export type Transaction = {
  id: number;
  card_id: number | null;
  user_id: number | null;
  meal_id: number | null;
  sonuc: string;
  islem_zamani: string;
  offline_senkron: boolean;
};
export type DailySummary = { basarili: number; red: number };

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Giriş başarısız");
  return res.json();
}

export async function fetchDevices(): Promise<Device[]> {
  const res = await fetch(`${API_URL}/devices`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Cihazlar alınamadı");
  return res.json();
}

export async function fetchRecentTransactions(): Promise<Transaction[]> {
  const res = await fetch(`${API_URL}/reports/transactions/recent?limit=30`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Geçişler alınamadı");
  return res.json();
}

export async function fetchTodaySummary(): Promise<DailySummary> {
  const res = await fetch(`${API_URL}/reports/summary/today`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Özet alınamadı");
  return res.json();
}
