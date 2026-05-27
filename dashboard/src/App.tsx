import { useEffect, useState } from "react";
import CustomersPanel from "./CustomersPanel";
import DashboardPanel from "./DashboardPanel";
import PosPanel from "./PosPanel";
import ProductsPanel from "./ProductsPanel";
import SalesPanel from "./SalesPanel";
import SettingsPanel from "./SettingsPanel";
import { fetchReports, getToken, login } from "./api";

type Tab = "dashboard" | "pos" | "products" | "sales" | "customers" | "reports" | "settings";

export default function App() {
  const [token, setToken] = useState(getToken());
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [tab, setTab] = useState<Tab>("dashboard");
  const [reports, setReports] = useState<{ today: string; week: string } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || tab !== "reports") return;
    (async () => {
      try {
        setReports(await fetchReports());
      } catch (e) {
        setError(String(e));
      }
    })();
  }, [token, tab]);

  const handleLogin = async () => {
    try {
      const res = await login(phone, password);
      localStorage.setItem("token", res.access_token);
      setToken(res.access_token);
      setError("");
    } catch {
      setError("Login failed");
    }
  };

  if (!token) {
    return (
      <div style={{ maxWidth: 360, margin: "4rem auto", padding: "1rem" }}>
        <h1>ShopBot Admin</h1>
        <div className="card" style={{ display: "grid", gap: "0.75rem" }}>
          <input placeholder="Phone (+255...)" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={handleLogin}>Sign in</button>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: tab === "pos" ? 1400 : 1200, margin: "0 auto", padding: "1.5rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>ShopBot Dashboard</h1>
        <button
          onClick={() => {
            localStorage.removeItem("token");
            setToken(null);
          }}
        >
          Logout
        </button>
      </header>

      <nav style={{ display: "flex", gap: "0.5rem", margin: "1rem 0", flexWrap: "wrap" }}>
        {(["dashboard", "pos", "products", "sales", "customers", "reports", "settings"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => {
              setTab(t);
              setError("");
            }}
            style={{ background: tab === t ? "#0f766e" : "#94a3b8" }}
          >
            {t}
          </button>
        ))}
      </nav>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {tab === "dashboard" && <DashboardPanel />}
      {tab === "pos" && <PosPanel />}
      {tab === "products" && <ProductsPanel />}
      {tab === "sales" && <SalesPanel />}
      {tab === "customers" && <CustomersPanel />}

      {tab === "reports" && reports && (
        <div className="card">
          <h2>Reports</h2>
          <pre style={{ whiteSpace: "pre-wrap" }}>{reports.today}</pre>
          <pre style={{ whiteSpace: "pre-wrap" }}>{reports.week}</pre>
        </div>
      )}

      {tab === "settings" && <SettingsPanel />}
    </div>
  );
}
