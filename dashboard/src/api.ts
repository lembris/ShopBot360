const API_BASE = import.meta.env.VITE_API_URL || "";

export type Product = {
  id: string;
  name: string;
  price: number;
  cost_price: number | null;
  stock_qty: number;
  reorder_at: number;
  unit: string;
  category: string | null;
};

export type ProductInput = {
  name: string;
  price: number;
  stock_qty: number;
  cost_price?: number | null;
  reorder_at?: number;
  unit?: string;
  category?: string | null;
};

export function getToken(): string | null {
  return localStorage.getItem("token");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function login(phone: string, password: string) {
  return api<{ access_token: string }>("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone, password }),
  });
}

export async function fetchProducts() {
  return api<Product[]>("/admin/products");
}

export async function createProduct(data: ProductInput) {
  return api<Product>("/admin/products", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProduct(id: string, data: Partial<ProductInput>) {
  return api<Product>(`/admin/products/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteProduct(id: string) {
  return api<{ status: string; id: string }>(`/admin/products/${id}`, {
    method: "DELETE",
  });
}

export async function fetchSales() {
  return api<SaleSummary[]>("/admin/sales");
}

export type SaleSummary = {
  id: string;
  receipt_no: string;
  customer_name: string | null;
  product_names: string;
  total_amount: number;
  payment_method: string;
  is_credit: boolean;
  sold_at: string | null;
};

export type SaleDetail = SaleSummary & {
  items: Array<{
    product_id: string;
    product_name: string;
    qty: number;
    unit_price: number;
    total: number;
  }>;
};

export async function fetchSale(id: string) {
  return api<SaleDetail>(`/admin/sales/${id}`);
}

export type Customer = {
  name: string;
  balance: number;
  total_sales: number;
  sale_count: number;
  last_sale_at: string | null;
};

export type CustomerDetail = {
  name: string;
  balance: number;
  ledger: Array<{
    id: string;
    type: string;
    amount: number;
    note: string | null;
    created_at: string | null;
  }>;
  sales: SaleSummary[];
};

export async function fetchCustomers() {
  return api<Customer[]>("/admin/customers");
}

export async function fetchCustomerDetail(name: string) {
  return api<CustomerDetail>(`/admin/customers/detail?name=${encodeURIComponent(name)}`);
}

export async function recordCustomerPayment(customer_name: string, amount: number, note?: string) {
  return api<{ status: string; customer_name: string; amount: number; balance: number }>(
    "/admin/customers/payment",
    {
      method: "POST",
      body: JSON.stringify({ customer_name, amount, note: note || null }),
    }
  );
}

export type PosCheckoutResult = {
  id: string;
  receipt_no: string;
  customer_name: string | null;
  total_amount: number;
  payment_method: string;
  is_credit: boolean;
  receipt_text: string;
  items: Array<{
    product_id: string;
    product_name: string;
    qty: number;
    unit_price: number;
    total: number;
  }>;
};

export async function checkoutPos(body: {
  items: Array<{ product_id: string; qty: number }>;
  payment_method: string;
  customer_name?: string | null;
}) {
  return api<PosCheckoutResult>("/admin/pos/checkout", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchReports() {
  return api<{ today: string; week: string }>("/admin/reports");
}

export async function setPassword(password: string) {
  return api<{ status: string }>("/admin/users/set-password", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export type DashboardData = {
  shop_name: string;
  currency: string;
  timezone: string;
  generated_at: string;
  today: {
    revenue: number;
    sales_count: number;
    avg_order_value: number;
    cost: number;
    profit: number;
    margin_pct: number;
  };
  week: {
    revenue: number;
    sales_count: number;
    avg_order_value: number;
    cost: number;
    profit: number;
    margin_pct: number;
  };
  all_time: { revenue: number; sales_count: number };
  inventory: {
    product_count: number;
    total_stock_units: number;
    stock_value: number;
    low_stock_count: number;
    low_stock: Array<{
      id: string;
      name: string;
      stock_qty: number;
      reorder_at: number;
      unit: string;
    }>;
  };
  debt: {
    total_outstanding: number;
    debtor_count: number;
    top_debtors: Array<{ name: string; balance: number }>;
  };
  daily_sales: Array<{
    date: string;
    label: string;
    revenue: number;
    sales_count: number;
  }>;
  top_products: Array<{ name: string; qty_sold: number; revenue: number }>;
  recent_sales: Array<{
    id: string;
    receipt_no: string;
    customer_name: string | null;
    product_names: string;
    total_amount: number;
    payment_method: string;
    is_credit: boolean;
    sold_at: string | null;
  }>;
};

export async function fetchDashboard() {
  return api<DashboardData>("/admin/dashboard");
}
