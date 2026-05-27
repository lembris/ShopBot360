import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SaleDetail, SaleSummary, fetchSale, fetchSales } from "./api";

function formatMoney(value: number) {
  return `${value.toLocaleString()} TZS`;
}

export default function SalesPanel() {
  const [sales, setSales] = useState<SaleSummary[]>([]);
  const [selected, setSelected] = useState<SaleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setSales(await fetchSales());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openSale = async (sale: SaleSummary) => {
    setDetailLoading(true);
    setError("");
    try {
      setSelected(await fetchSale(sale.id));
    } catch (e) {
      setError(String(e));
    } finally {
      setDetailLoading(false);
    }
  };

  const chartData = sales.slice(0, 7).map((s) => ({
    name: s.receipt_no.split("-").pop() || s.receipt_no,
    amount: s.total_amount,
  }));

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Sales</h2>
          <button type="button" className="secondary" onClick={load}>
            Refresh
          </button>
        </div>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
            <thead>
              <tr>
                <th align="left">Receipt</th>
                <th align="left">Products</th>
                <th align="left">Customer</th>
                <th align="left">Payment</th>
                <th align="right">Amount</th>
                <th align="left">When</th>
                <th align="right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sales.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.receipt_no}</td>
                  <td>{sale.product_names || "—"}</td>
                  <td>{sale.customer_name || "Walk-in"}</td>
                  <td>{sale.is_credit ? "Credit" : sale.payment_method}</td>
                  <td align="right">{formatMoney(sale.total_amount)}</td>
                  <td>{sale.sold_at ? new Date(sale.sold_at).toLocaleString() : "—"}</td>
                  <td align="right">
                    <button type="button" className="secondary" onClick={() => openSale(sale)}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && sales.length === 0 && <p>No sales recorded yet.</p>}
        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </div>

      <div className="card" style={{ height: 280 }}>
        <h3>Recent sales chart</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip formatter={(value: number) => formatMoney(value)} />
            <Bar dataKey="amount" fill="#0d9488" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {(selected || detailLoading) && (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3>Sale detail</h3>
            <button type="button" className="secondary" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          {detailLoading && <p>Loading receipt...</p>}
          {selected && (
            <>
              <p>
                <strong>{selected.receipt_no}</strong> ·{" "}
                {selected.customer_name || "Walk-in"} ·{" "}
                {selected.is_credit ? "Credit" : selected.payment_method}
              </p>
              <p style={{ color: "#64748b" }}>
                {selected.sold_at ? new Date(selected.sold_at).toLocaleString() : "—"}
              </p>
              <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
                <thead>
                  <tr>
                    <th align="left">Product</th>
                    <th align="right">Qty</th>
                    <th align="right">Unit price</th>
                    <th align="right">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.items.map((item) => (
                    <tr key={item.product_id + item.qty}>
                      <td>{item.product_name}</td>
                      <td align="right">{item.qty}</td>
                      <td align="right">{formatMoney(item.unit_price)}</td>
                      <td align="right">{formatMoney(item.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p style={{ textAlign: "right", fontWeight: 700, marginTop: "1rem" }}>
                Total: {formatMoney(selected.total_amount)}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
