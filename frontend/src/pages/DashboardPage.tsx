import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  DailySummary,
  Device,
  Transaction,
  fetchDevices,
  fetchRecentTransactions,
  fetchTodaySummary,
} from "../api/client";

export default function DashboardPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
    const load = async () => {
      try {
        const [d, t, s] = await Promise.all([
          fetchDevices(),
          fetchRecentTransactions(),
          fetchTodaySummary(),
        ]);
        setDevices(d);
        setTxs(t);
        setSummary(s);
      } catch {
        localStorage.removeItem("token");
        navigate("/login");
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [navigate]);

  function logout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Canlı İzleme</h1>
        <button onClick={logout} className="text-sm text-slate-600 underline">
          Çıkış
        </button>
      </header>

      {summary && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-slate-500">Bugün başarılı geçiş</p>
            <p className="text-3xl font-bold text-green-700">{summary.basarili}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-slate-500">Bugün red</p>
            <p className="text-3xl font-bold text-red-700">{summary.red}</p>
          </div>
        </div>
      )}

      <section className="bg-white rounded-lg shadow overflow-hidden">
        <h2 className="px-4 py-3 font-medium border-b">Cihazlar</h2>
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="p-3">Konum</th>
              <th className="p-3">Durum</th>
              <th className="p-3">Son iletişim</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id} className="border-t">
                <td className="p-3">{d.konum}</td>
                <td className="p-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs ${
                      d.online ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    }`}
                  >
                    {d.online ? "Çevrimiçi" : "Çevrimdışı"}
                  </span>
                </td>
                <td className="p-3">{d.son_iletisim ? new Date(d.son_iletisim).toLocaleString("tr-TR") : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="bg-white rounded-lg shadow overflow-hidden">
        <h2 className="px-4 py-3 font-medium border-b">Son geçişler</h2>
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="p-3">Zaman</th>
              <th className="p-3">Sonuç</th>
              <th className="p-3">Offline</th>
            </tr>
          </thead>
          <tbody>
            {txs.map((t) => (
              <tr key={t.id} className="border-t">
                <td className="p-3">{new Date(t.islem_zamani).toLocaleString("tr-TR")}</td>
                <td className="p-3">{t.sonuc}</td>
                <td className="p-3">{t.offline_senkron ? "Evet" : "Hayır"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <p className="text-xs text-slate-500">
        Grafana:{" "}
        <a href="http://localhost:3001" target="_blank" rel="noreferrer" className="underline">
          localhost:3001
        </a>
      </p>
    </div>
  );
}
