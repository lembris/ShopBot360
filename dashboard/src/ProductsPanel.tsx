import { FormEvent, useEffect, useState } from "react";
import {
  Product,
  ProductInput,
  createProduct,
  deleteProduct,
  fetchProducts,
  updateProduct,
} from "./api";

const emptyForm: ProductInput = {
  name: "",
  price: 0,
  stock_qty: 0,
  cost_price: null,
  reorder_at: 5,
  unit: "pcs",
  category: "",
};

export default function ProductsPanel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [form, setForm] = useState<ProductInput>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadProducts = async () => {
    setLoading(true);
    setError("");
    try {
      setProducts(await fetchProducts());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");
    const payload: ProductInput = {
      name: form.name.trim(),
      price: Number(form.price),
      stock_qty: Number(form.stock_qty),
      cost_price: form.cost_price ? Number(form.cost_price) : null,
      reorder_at: Number(form.reorder_at ?? 5),
      unit: form.unit?.trim() || "pcs",
      category: form.category?.trim() || null,
    };

    try {
      if (editingId) {
        await updateProduct(editingId, payload);
        setMessage("Product updated.");
      } else {
        await createProduct(payload);
        setMessage("Product added.");
      }
      resetForm();
      await loadProducts();
    } catch (e) {
      setError(String(e));
    }
  };

  const startEdit = (product: Product) => {
    setEditingId(product.id);
    setForm({
      name: product.name,
      price: product.price,
      stock_qty: product.stock_qty,
      cost_price: product.cost_price,
      reorder_at: product.reorder_at,
      unit: product.unit,
      category: product.category ?? "",
    });
    setMessage("");
    setError("");
  };

  const handleDelete = async (product: Product) => {
    if (!confirm(`Remove "${product.name}" from the shop?`)) return;
    setError("");
    setMessage("");
    try {
      await deleteProduct(product.id);
      if (editingId === product.id) resetForm();
      setMessage(`Removed ${product.name}.`);
      await loadProducts();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <div className="card">
        <h2>{editingId ? "Edit product" : "Add product"}</h2>
        <form
          onSubmit={handleSubmit}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: "0.75rem",
            marginTop: "1rem",
          }}
        >
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Name</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Price (TZS)</span>
            <input
              required
              type="number"
              min="0"
              step="1"
              value={form.price}
              onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Cost price</span>
            <input
              type="number"
              min="0"
              step="1"
              value={form.cost_price ?? ""}
              onChange={(e) =>
                setForm({
                  ...form,
                  cost_price: e.target.value ? Number(e.target.value) : null,
                })
              }
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Stock qty</span>
            <input
              required
              type="number"
              min="0"
              step="1"
              value={form.stock_qty}
              onChange={(e) => setForm({ ...form, stock_qty: Number(e.target.value) })}
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Reorder at</span>
            <input
              type="number"
              min="0"
              step="1"
              value={form.reorder_at ?? 5}
              onChange={(e) => setForm({ ...form, reorder_at: Number(e.target.value) })}
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Unit</span>
            <input
              value={form.unit ?? "pcs"}
              onChange={(e) => setForm({ ...form, unit: e.target.value })}
            />
          </label>
          <label style={{ display: "grid", gap: "0.25rem" }}>
            <span>Category</span>
            <input
              value={form.category ?? ""}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
          </label>
          <div style={{ display: "flex", alignItems: "end", gap: "0.5rem" }}>
            <button type="submit">{editingId ? "Save changes" : "Add product"}</button>
            {editingId && (
              <button type="button" className="secondary" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
        {message && <p style={{ color: "#0f766e", marginTop: "0.75rem" }}>{message}</p>}
        {error && <p style={{ color: "crimson", marginTop: "0.75rem" }}>{error}</p>}
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Products</h2>
          <button type="button" className="secondary" onClick={loadProducts}>
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
                <th align="right">Price</th>
                <th align="right">Cost</th>
                <th align="right">Stock</th>
                <th align="right">Reorder</th>
                <th align="left">Unit</th>
                <th align="right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td align="right">{product.price.toLocaleString()}</td>
                  <td align="right">
                    {product.cost_price != null ? product.cost_price.toLocaleString() : "—"}
                  </td>
                  <td align="right">{product.stock_qty}</td>
                  <td align="right">{product.reorder_at}</td>
                  <td>{product.unit}</td>
                  <td align="right">
                    <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                      <button type="button" className="secondary" onClick={() => startEdit(product)}>
                        Edit
                      </button>
                      <button type="button" className="danger" onClick={() => handleDelete(product)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && products.length === 0 && <p>No products yet. Add your first product above.</p>}
      </div>
    </div>
  );
}
