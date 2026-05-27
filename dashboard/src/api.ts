const API_BASE = import.meta.env.VITE_API_URL || "";

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
  return res.json();
}

export async function login(phone: string, password: string) {
  return api<{ access_token: string }>("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({ phone, password }),
  });
}

export async function fetchProducts() {
  return api<Array<{ id: string; name: string; price: number; stock_qty: number }>>(
    "/admin/products"
  );
}

export async function fetchSales() {
  return api<
    Array<{ id: string; receipt_no: string; total_amount: number; sold_at: string | null }>
  >("/admin/sales");
}

export async function fetchReports() {
  return api<{ today: string; week: string }>("/admin/reports");
}
