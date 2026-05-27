import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DashboardData, fetchDashboard } from "./api";

function formatMoney(value: number, currency = "TZS") {
  return `${value.toLocaleString()} ${currency}`;
}

function KpiCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "warn" | "good";
}) {
  return (
    <div className={`kpi-card kpi-${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}

export default function DashboardPanel() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setData(await fetchDashboard());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <div className="card">Loading dashboard...</div>;
  if (error) return <div className="card"><p style={{ color: "crimson" }}>{error}</p></div>;
  if (!data) return null;

  const currency = data.currency;

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <div className="card" style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0 }}>{data.shop_name}</h2>
          <p style={{ margin: "0.35rem 0 0", color: "#64748b" }}>
            Business overview · {data.timezone}
          </p>
        </div>
        <button type="button" className="secondary" onClick={load}>
          Refresh
        </button>
      </div>

      <section>
        <h3>Today</h3>
        <div className="kpi-grid">
          <KpiCard label="Revenue" value={formatMoney(data.today.revenue, currency)} />
          <KpiCard label="Profit" value={formatMoney(data.today.profit, currency)} tone="good" />
          <KpiCard label="Sales" value={String(data.today.sales_count)} hint="transactions" />
          <KpiCard
            label="Margin"
            value={`${data.today.margin_pct}%`}
            hint={`Cost ${formatMoney(data.today.cost, currency)}`}
          />
          <KpiCard
            label="Avg order"
            value={formatMoney(data.today.avg_order_value, currency)}
          />
        </div>
      </section>

      <section>
        <h3>This week</h3>
        <div className="kpi-grid">
          <KpiCard label="Revenue" value={formatMoney(data.week.revenue, currency)} />
          <KpiCard label="Profit" value={formatMoney(data.week.profit, currency)} tone="good" />
          <KpiCard label="Sales" value={String(data.week.sales_count)} />
          <KpiCard label="All-time revenue" value={formatMoney(data.all_time.revenue, currency)} />
        </div>
      </section>

      <div className="dashboard-grid">
        <div className="card chart-card">
          <h3>7-day sales trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.daily_sales}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatMoney(value, currency)} />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#0d9488" strokeWidth={2} name="Revenue" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3>Top products by revenue</h3>
          {data.top_products.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.top_products}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value: number) => formatMoney(value, currency)} />
                <Bar dataKey="revenue" fill="#0284c7" name="Revenue" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p>No product sales yet.</p>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Inventory snapshot</h3>
          <div className="kpi-grid compact">
            <KpiCard label="Products" value={String(data.inventory.product_count)} />
            <KpiCard label="Stock units" value={String(data.inventory.total_stock_units)} />
            <KpiCard label="Stock value" value={formatMoney(data.inventory.stock_value, currency)} />
            <KpiCard
              label="Low stock"
              value={String(data.inventory.low_stock_count)}
              tone={data.inventory.low_stock_count > 0 ? "warn" : "default"}
            />
          </div>
          {data.inventory.low_stock.length > 0 && (
            <>
              <h4>Needs restock</h4>
              <ul>
                {data.inventory.low_stock.map((item) => (
                  <li key={item.id}>
                    {item.name}: {item.stock_qty} {item.unit} (reorder at {item.reorder_at})
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        <div className="card">
          <h3>Outstanding credit</h3>
          <div className="kpi-grid compact">
            <KpiCard
              label="Total owed"
              value={formatMoney(data.debt.total_outstanding, currency)}
              tone={data.debt.total_outstanding > 0 ? "warn" : "default"}
            />
            <KpiCard label="Debtors" value={String(data.debt.debtor_count)} />
          </div>
          {data.debt.top_debtors.length > 0 ? (
            <ul>
              {data.debt.top_debtors.map((debtor) => (
                <li key={debtor.name}>
                  {debtor.name} — {formatMoney(debtor.balance, currency)}
                </li>
              ))}
            </ul>
          ) : (
            <p>No outstanding customer debt.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Recent sales</h3>
        {data.recent_sales.length > 0 ? (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Receipt</th>
                <th align="left">Products</th>
                <th align="left">Customer</th>
                <th align="left">Payment</th>
                <th align="right">Amount</th>
                <th align="left">When</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_sales.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.receipt_no}</td>
                  <td>{sale.product_names || "—"}</td>
                  <td>{sale.customer_name || "Walk-in"}</td>
                  <td>{sale.is_credit ? "Credit" : sale.payment_method}</td>
                  <td align="right">{formatMoney(sale.total_amount, currency)}</td>
                  <td>{sale.sold_at ? new Date(sale.sold_at).toLocaleString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No sales recorded yet.</p>
        )}
      </div>
    </div>
  );
}
