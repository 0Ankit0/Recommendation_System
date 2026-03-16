const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchCategories() {
  const res = await fetch(`${API}/api/categories`, { cache: 'no-store' });
  return res.json();
}

export async function fetchProducts() {
  const res = await fetch(`${API}/api/products`, { cache: 'no-store' });
  return res.json();
}

export async function addToCart(userId: string, productId: number, quantity = 1) {
  const res = await fetch(`${API}/api/cart/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, product_id: productId, quantity })
  });
  return res.json();
}

export async function fetchCart(userId: string) {
  const res = await fetch(`${API}/api/cart/user/${userId}`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}
