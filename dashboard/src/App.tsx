import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  fetchProducts,
  fetchReports,
  fetchSales,
  getToken,
  login,
} from "./api";

type Tab = "products" | "sales" | "reports";

export default function App() {
  const [token, setToken] = useState(getToken());
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [tab, setTab] = useState<Tab>("products");
  const [products, setProducts] = useState<
    Array<{ id: string; name: string; price: number; stock_qty: number }>
  >([]);
  const [sales, setSales] = useState<
    Array<{ receipt_no: string; total_amount: number; sold_at: string | null }>
  >([]);
  const [reports, setReports] = useState<{ today: string; week: string } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        if (tab === "products") setProducts(await fetchProducts());
        if (tab === "sales") setSales(await fetchSales());
        if (tab === "reports") setReports(await fetchReports());
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
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button onClick={handleLogin}>Sign in</button>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
        </div>
      </div>
    );
  }

  const chartData = sales.slice(0, 7).map((s) => ({
    name: s.receipt_no.split("-").pop() || s.receipt_no,
    amount: s.total_amount,
  }));

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "1.5rem" }}>
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

      <nav style={{ display: "flex", gap: "0.5rem", margin: "1rem 0" }}>
        {(["products", "sales", "reports"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{ background: tab === t ? "#0f766e" : "#94a3b8" }}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "products" && (
        <div className="card">
          <h2>Products</h2>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Name</th>
                <th align="right">Price</th>
                <th align="right">Stock</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td align="right">{p.price.toLocaleString()} TZS</td>
                  <td align="right">{p.stock_qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "sales" && (
        <>
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2>Recent sales</h2>
            <ul>
              {sales.map((s) => (
                <li key={s.receipt_no}>
                  {s.receipt_no} — {s.total_amount.toLocaleString()} TZS
                </li>
              ))}
            </ul>
          </div>
          <div className="card" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="amount" fill="#0d9488" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {tab === "reports" && reports && (
        <div className="card">
          <h2>Reports</h2>
          <pre style={{ whiteSpace: "pre-wrap" }}>{reports.today}</pre>
          <pre style={{ whiteSpace: "pre-wrap" }}>{reports.week}</pre>
        </div>
      )}
    </div>
  );
}
