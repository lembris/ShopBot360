import { FormEvent, useEffect, useState } from "react";
import {
  Customer,
  CustomerDetail,
  fetchCustomerDetail,
  fetchCustomers,
  recordCustomerPayment,
} from "./api";

function formatMoney(value: number) {
  return `${value.toLocaleString()} TZS`;
}

export default function CustomersPanel() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selected, setSelected] = useState<CustomerDetail | null>(null);
  const [paymentName, setPaymentName] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentNote, setPaymentNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setCustomers(await fetchCustomers());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCustomer = async (customer: Customer) => {
    setDetailLoading(true);
    setPaymentName(customer.name);
    setError("");
    try {
      setSelected(await fetchCustomerDetail(customer.name));
    } catch (e) {
      setError(String(e));
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePayment = async (event: FormEvent) => {
    event.preventDefault();
    setMessage("");
    setError("");
    try {
      const result = await recordCustomerPayment(
        paymentName,
        Number(paymentAmount),
        paymentNote || undefined
      );
      setMessage(
        `Recorded ${formatMoney(result.amount)} from ${result.customer_name}. Balance: ${formatMoney(result.balance)}`
      );
      setPaymentAmount("");
      setPaymentNote("");
      await load();
      if (paymentName) setSelected(await fetchCustomerDetail(paymentName));
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Customers</h2>
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
                <th align="left">Name</th>
                <th align="right">Balance owed</th>
                <th align="right">Total sales</th>
                <th align="right">Orders</th>
                <th align="left">Last sale</th>
                <th align="right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((customer) => (
                <tr key={customer.name}>
                  <td>{customer.name}</td>
                  <td align="right" style={{ color: customer.balance > 0 ? "#c2410c" : undefined }}>
                    {formatMoney(customer.balance)}
                  </td>
                  <td align="right">{formatMoney(customer.total_sales)}</td>
                  <td align="right">{customer.sale_count}</td>
                  <td>
                    {customer.last_sale_at
                      ? new Date(customer.last_sale_at).toLocaleString()
                      : "—"}
                  </td>
                  <td align="right">
                    <button type="button" className="secondary" onClick={() => openCustomer(customer)}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && customers.length === 0 && (
          <p>No customers yet. Add a customer name when selling on credit via WhatsApp.</p>
        )}
      </div>

      <div className="card">
        <h3>Record payment</h3>
        <form
          onSubmit={handlePayment}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "0.75rem",
            marginTop: "1rem",
          }}
        >
          <input
            required
            placeholder="Customer name"
            value={paymentName}
            onChange={(e) => setPaymentName(e.target.value)}
          />
          <input
            required
            type="number"
            min="1"
            placeholder="Amount"
            value={paymentAmount}
            onChange={(e) => setPaymentAmount(e.target.value)}
          />
          <input
            placeholder="Note (optional)"
            value={paymentNote}
            onChange={(e) => setPaymentNote(e.target.value)}
          />
          <button type="submit">Record payment</button>
        </form>
        {message && <p style={{ color: "#0f766e" }}>{message}</p>}
        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </div>

      {(selected || detailLoading) && (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3>{selected?.name || paymentName}</h3>
            <button type="button" className="secondary" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          {detailLoading && <p>Loading customer...</p>}
          {selected && (
            <>
              <p>
                Balance owed:{" "}
                <strong style={{ color: selected.balance > 0 ? "#c2410c" : "#0f766e" }}>
                  {formatMoney(selected.balance)}
                </strong>
              </p>

              <h4>Recent sales</h4>
              {selected.sales.length > 0 ? (
                <ul>
                  {selected.sales.map((sale) => (
                    <li key={sale.id}>
                      {sale.receipt_no} — {sale.product_names || "—"} — {formatMoney(sale.total_amount)} (
                      {sale.is_credit ? "Credit" : sale.payment_method})
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No sales linked to this customer.</p>
              )}

              <h4>Credit ledger</h4>
              {selected.ledger.length > 0 ? (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th align="left">Type</th>
                      <th align="right">Amount</th>
                      <th align="left">Note</th>
                      <th align="left">When</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.ledger.map((entry) => (
                      <tr key={entry.id}>
                        <td>{entry.type}</td>
                        <td align="right">{formatMoney(entry.amount)}</td>
                        <td>{entry.note || "—"}</td>
                        <td>
                          {entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No ledger entries yet.</p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
