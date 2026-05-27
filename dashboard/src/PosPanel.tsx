import { useEffect, useMemo, useState } from "react";
import { Product, PosCheckoutResult, checkoutPos, fetchProducts } from "./api";

type CartLine = {
  product: Product;
  qty: number;
};

function formatMoney(value: number) {
  return `${value.toLocaleString()} TZS`;
}

export default function PosPanel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [paymentMethod, setPaymentMethod] = useState<"cash" | "credit" | "mobile">("cash");
  const [customerName, setCustomerName] = useState("");
  const [loading, setLoading] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<PosCheckoutResult | null>(null);

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

  const categories = useMemo(() => {
    const values = new Set<string>();
    products.forEach((p) => {
      if (p.category) values.add(p.category);
    });
    return ["all", ...Array.from(values).sort()];
  }, [products]);

  const filteredProducts = useMemo(() => {
    const q = search.trim().toLowerCase();
    return products.filter((p) => {
      if (category !== "all" && p.category !== category) return false;
      if (!q) return true;
      return p.name.toLowerCase().includes(q) || (p.category || "").toLowerCase().includes(q);
    });
  }, [products, search, category]);

  const cartTotal = cart.reduce((sum, line) => sum + line.product.price * line.qty, 0);
  const cartCount = cart.reduce((sum, line) => sum + line.qty, 0);

  const addToCart = (product: Product) => {
    if (product.stock_qty <= 0) return;
    setCart((prev) => {
      const existing = prev.find((line) => line.product.id === product.id);
      if (existing) {
        if (existing.qty >= product.stock_qty) return prev;
        return prev.map((line) =>
          line.product.id === product.id ? { ...line, qty: line.qty + 1 } : line
        );
      }
      return [...prev, { product, qty: 1 }];
    });
  };

  const changeQty = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((line) => {
          if (line.product.id !== productId) return line;
          const nextQty = line.qty + delta;
          if (nextQty <= 0) return null;
          if (nextQty > line.product.stock_qty) return line;
          return { ...line, qty: nextQty };
        })
        .filter(Boolean) as CartLine[]
    );
  };

  const removeLine = (productId: string) => {
    setCart((prev) => prev.filter((line) => line.product.id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setCustomerName("");
    setPaymentMethod("cash");
  };

  const handleCheckout = async () => {
    if (cart.length === 0) {
      setError("Add products to the cart first.");
      return;
    }
    if (paymentMethod === "credit" && !customerName.trim()) {
      setError("Customer name is required for credit sales.");
      return;
    }

    setCheckingOut(true);
    setError("");
    try {
      const result = await checkoutPos({
        items: cart.map((line) => ({ product_id: line.product.id, qty: line.qty })),
        payment_method: paymentMethod,
        customer_name: customerName.trim() || null,
      });
      setReceipt(result);
      clearCart();
      await loadProducts();
    } catch (e) {
      setError(String(e));
    } finally {
      setCheckingOut(false);
    }
  };

  return (
    <div className="pos-layout">
      <section className="card pos-products">
        <div className="pos-toolbar">
          <h2>Point of Sale</h2>
          <button type="button" className="secondary" onClick={loadProducts}>
            Refresh
          </button>
        </div>

        <div className="pos-filters">
          <input
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c === "all" ? "All categories" : c}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p>Loading products...</p>
        ) : (
          <div className="pos-grid">
            {filteredProducts.map((product) => {
              const outOfStock = product.stock_qty <= 0;
              return (
                <button
                  key={product.id}
                  type="button"
                  className={`pos-product-card${outOfStock ? " out-of-stock" : ""}`}
                  onClick={() => addToCart(product)}
                  disabled={outOfStock}
                >
                  <span className="pos-product-name">{product.name}</span>
                  <span className="pos-product-price">{formatMoney(product.price)}</span>
                  <span className="pos-product-stock">
                    {outOfStock ? "Out of stock" : `${product.stock_qty} ${product.unit} left`}
                  </span>
                  {product.category && <span className="pos-product-category">{product.category}</span>}
                </button>
              );
            })}
          </div>
        )}
        {!loading && filteredProducts.length === 0 && <p>No products match your search.</p>}
      </section>

      <section className="card pos-cart">
        <div className="pos-toolbar">
          <h2>Cart ({cartCount})</h2>
          <button type="button" className="secondary" onClick={clearCart} disabled={cart.length === 0}>
            Clear
          </button>
        </div>

        {cart.length === 0 ? (
          <p className="pos-empty">Tap products to add them here.</p>
        ) : (
          <div className="pos-cart-lines">
            {cart.map((line) => (
              <div key={line.product.id} className="pos-cart-line">
                <div>
                  <strong>{line.product.name}</strong>
                  <div className="pos-line-meta">
                    {formatMoney(line.product.price)} each
                  </div>
                </div>
                <div className="pos-qty-controls">
                  <button type="button" className="secondary" onClick={() => changeQty(line.product.id, -1)}>
                    −
                  </button>
                  <span>{line.qty}</span>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => changeQty(line.product.id, 1)}
                    disabled={line.qty >= line.product.stock_qty}
                  >
                    +
                  </button>
                </div>
                <div className="pos-line-total">{formatMoney(line.product.price * line.qty)}</div>
                <button type="button" className="danger" onClick={() => removeLine(line.product.id)}>
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="pos-checkout">
          <label>
            Payment method
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as "cash" | "credit" | "mobile")}
            >
              <option value="cash">Cash</option>
              <option value="mobile">Mobile money</option>
              <option value="credit">Credit (debt)</option>
            </select>
          </label>

          {paymentMethod === "credit" && (
            <label>
              Customer name
              <input
                placeholder="Who is buying on credit?"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
              />
            </label>
          )}

          <div className="pos-total-row">
            <span>Total</span>
            <strong>{formatMoney(cartTotal)}</strong>
          </div>

          <button type="button" onClick={handleCheckout} disabled={checkingOut || cart.length === 0}>
            {checkingOut ? "Processing..." : "Complete sale"}
          </button>
        </div>

        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </section>

      {receipt && (
        <div className="pos-receipt-overlay" onClick={() => setReceipt(null)}>
          <div className="card pos-receipt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="pos-toolbar">
              <h3>Sale complete</h3>
              <button type="button" className="secondary" onClick={() => setReceipt(null)}>
                Close
              </button>
            </div>
            <p>
              <strong>{receipt.receipt_no}</strong>
            </p>
            <pre className="pos-receipt-text">{receipt.receipt_text}</pre>
            <button type="button" onClick={() => setReceipt(null)}>
              New sale
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
