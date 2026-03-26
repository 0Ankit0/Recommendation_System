const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type Category = {
  id: number;
  name: string;
  sub_categories?: Category[];
};

export type ProductImage = {
  image_id: number;
  url: string;
  is_primary: boolean;
  product_id: number;
};

export type Product = {
  product_id: number;
  name: string;
  description?: string | null;
  price: number;
  stock_quantity: number;
  category_id: number;
  images: ProductImage[];
};

export type Cart = {
  cart_id: string;
  user_id: string;
  items: { product_id: number; quantity: number }[];
};

export type RecommendationEnvelope = {
  userId: string;
  recommendations: {
    itemId: number;
    score: number;
    rank: number;
    explanation?: string | null;
  }[];
  metadata: Record<string, string>;
};

export type UserPreference = {
  userId: string;
  categories: string[];
  diversity: number;
  recency_bias: number;
  excludeViewed: boolean;
  algorithm?: 'collaborative' | 'content_based' | 'hybrid' | null;
  maxPerCategory: number;
  updatedAt: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    cache: 'no-store',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {})
    }
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {}
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export function fetchCategories() {
  return request<Category[]>('/api/categories');
}

export function fetchProducts(limit = 24) {
  return request<Product[]>(`/api/products?limit=${limit}`);
}

export function fetchCart(userId: string) {
  return request<Cart>(`/api/cart/user/${encodeURIComponent(userId)}`).catch(() => null);
}

export function addToCart(userId: string, productId: number, quantity = 1) {
  return request<Cart>('/api/cart/add', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, product_id: productId, quantity })
  });
}

export function fetchRecommendations(
  userId: string,
  options?: { algorithm?: string; limit?: number; explain?: boolean }
) {
  const params = new URLSearchParams();
  if (options?.algorithm) params.set('algorithm', options.algorithm);
  if (options?.limit) params.set('limit', String(options.limit));
  if (typeof options?.explain === 'boolean') params.set('explain', String(options.explain));
  const query = params.toString();
  return request<RecommendationEnvelope>(`/v1/recommendations/${encodeURIComponent(userId)}${query ? `?${query}` : ''}`);
}

export function fetchPreferences(userId: string) {
  return request<UserPreference>(`/v1/users/${encodeURIComponent(userId)}/preferences`);
}

export function savePreferences(userId: string, preference: Omit<UserPreference, 'userId' | 'updatedAt'>) {
  return request<UserPreference>(`/v1/users/${encodeURIComponent(userId)}/preferences`, {
    method: 'PUT',
    body: JSON.stringify(preference)
  });
}

export function trackEvent(payload: {
  eventId?: string;
  userId: string;
  itemId: number;
  actionType: 'view' | 'click' | 'search' | 'comment' | 'cart' | 'purchase' | 'like' | 'save' | 'share';
  value?: number;
  context?: Record<string, unknown>;
}) {
  return request<{ eventId: string; status: string }>('/v1/events', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}
