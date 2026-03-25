'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  addToCart,
  Category,
  fetchCart,
  fetchCategories,
  fetchPreferences,
  fetchProducts,
  fetchRecommendations,
  Product,
  RecommendationEnvelope,
  savePreferences,
  trackEvent,
  UserPreference
} from '@/components/api';

const DEFAULT_USER = 'demo-user';

const EMPTY_PREFERENCE: Omit<UserPreference, 'userId' | 'updatedAt'> = {
  categories: [],
  diversity: 0.3,
  recency_bias: 0.5,
  excludeViewed: false,
  algorithm: 'hybrid',
  maxPerCategory: 3
};

export default function HomePage() {
  const [userId, setUserId] = useState(DEFAULT_USER);
  const [activeUserId, setActiveUserId] = useState(DEFAULT_USER);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Awaited<ReturnType<typeof fetchCart>>>(null);
  const [recommendations, setRecommendations] = useState<RecommendationEnvelope | null>(null);
  const [preference, setPreference] = useState<Omit<UserPreference, 'userId' | 'updatedAt'>>(EMPTY_PREFERENCE);
  const [loading, setLoading] = useState(true);
  const [savingPreference, setSavingPreference] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const categoryOptions = useMemo(() => flattenCategories(categories), [categories]);
  const recommendedProducts = useMemo(() => {
    const lookup = new Map(products.map((product) => [product.product_id, product]));
    return (recommendations?.recommendations || [])
      .map((row) => ({
        recommendation: row,
        product: lookup.get(row.itemId)
      }))
      .filter((row): row is { recommendation: RecommendationEnvelope['recommendations'][number]; product: Product } => Boolean(row.product));
  }, [products, recommendations]);

  const loadDashboard = useCallback(async (nextUserId: string, algorithm?: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const [categoryRows, productRows, cartRow, preferenceRow] = await Promise.all([
        fetchCategories(),
        fetchProducts(),
        fetchCart(nextUserId),
        fetchPreferences(nextUserId)
      ]);
      const resolvedAlgorithm = preferenceRow.algorithm || algorithm || 'hybrid';
      const recommendationRow = await fetchRecommendations(nextUserId, {
        algorithm: resolvedAlgorithm,
        limit: 8,
        explain: true
      });

      setCategories(categoryRows);
      setProducts(productRows);
      setCart(cartRow);
      setPreference({
        categories: preferenceRow.categories,
        diversity: preferenceRow.diversity,
        recency_bias: preferenceRow.recency_bias,
        excludeViewed: preferenceRow.excludeViewed,
        algorithm: preferenceRow.algorithm || 'hybrid',
        maxPerCategory: preferenceRow.maxPerCategory
      });
      setRecommendations(recommendationRow);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load the recommendation dashboard.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard(activeUserId);
  }, [activeUserId, loadDashboard]);

  const refreshRecommendations = useCallback(async (nextUserId: string, algorithm?: string | null) => {
    const recommendationRow = await fetchRecommendations(nextUserId, {
      algorithm: algorithm || undefined,
      limit: 8,
      explain: true
    });
    setRecommendations(recommendationRow);
  }, []);

  const onAdd = async (productId: number) => {
    try {
      setError(null);
      await addToCart(activeUserId, productId, 1);
      await trackEvent({
        eventId: createEventId('cart', activeUserId, productId),
        userId: activeUserId,
        itemId: productId,
        actionType: 'cart',
        context: { source: 'frontend_nextjs' }
      });
      const nextCart = await fetchCart(activeUserId);
      setCart(nextCart);
      await refreshRecommendations(activeUserId, preference.algorithm);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : 'Unable to add item to cart.');
    }
  };

  const onPreviewRecommendation = async (productId: number) => {
    try {
      await trackEvent({
        eventId: createEventId('view', activeUserId, productId),
        userId: activeUserId,
        itemId: productId,
        actionType: 'view',
        context: { placement: 'recommendations' }
      });
      await refreshRecommendations(activeUserId, preference.algorithm);
    } catch (trackError) {
      setError(trackError instanceof Error ? trackError.message : 'Unable to record the recommendation preview.');
    }
  };

  const onSavePreferences = async () => {
    try {
      setSavingPreference(true);
      setError(null);
      const saved = await savePreferences(activeUserId, preference);
      setPreference({
        categories: saved.categories,
        diversity: saved.diversity,
        recency_bias: saved.recency_bias,
        excludeViewed: saved.excludeViewed,
        algorithm: saved.algorithm || 'hybrid',
        maxPerCategory: saved.maxPerCategory
      });
      await refreshRecommendations(activeUserId, saved.algorithm);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Unable to save preferences.');
    } finally {
      setSavingPreference(false);
    }
  };

  return (
    <main>
      <div className="hero">
        <div>
          <p className="eyebrow">Smart recommendation engine</p>
          <h1>Docs-aligned recommendation dashboard</h1>
          <p className="subtitle">
            Explore products, capture events, tune ranking preferences, and inspect the live recommendation output.
          </p>
        </div>
        <div className="card">
          <label className="stack">
            <span>User ID</span>
            <div className="row">
              <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="Enter a user ID" />
              <button
                onClick={() => setActiveUserId(userId.trim() || DEFAULT_USER)}
                disabled={!userId.trim() || loading}
              >
                Load
              </button>
            </div>
          </label>
          <p className="muted">Active user: <strong>{activeUserId}</strong></p>
        </div>
      </div>

      {error ? <section className="card error-banner">{error}</section> : null}

      <section className="card">
        <div className="section-header">
          <h2>Recommendation feed</h2>
          {recommendations?.metadata?.modelVersion ? (
            <span className="badge">
              {recommendations.metadata.algorithm} · {recommendations.metadata.modelVersion}
            </span>
          ) : null}
        </div>
        {loading ? (
          <div className="state">Loading recommendations…</div>
        ) : recommendedProducts.length === 0 ? (
          <div className="state">No recommendations available yet. Add events or products to improve personalization.</div>
        ) : (
          <div className="grid">
            {recommendedProducts.map(({ recommendation, product }) => (
              <article key={product.product_id} className="card nested-card">
                <div className="space-between">
                  <strong>{product.name}</strong>
                  <span className="badge">#{recommendation.rank}</span>
                </div>
                <p className="muted">${product.price.toFixed(2)} · category {product.category_id}</p>
                <p>{recommendation.explanation || 'Recommended from recent activity.'}</p>
                <div className="row">
                  <button onClick={() => void onPreviewRecommendation(product.product_id)}>Track view</button>
                  <button onClick={() => void onAdd(product.product_id)}>Add to cart</button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <div className="section-header">
          <h2>Preference controls</h2>
          <span className="badge">Personalization</span>
        </div>
        <div className="grid">
          <label className="stack">
            <span>Preferred categories</span>
            <select
              multiple
              value={preference.categories}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  categories: Array.from(event.target.selectedOptions).map((option) => option.value)
                }))
              }
            >
              {categoryOptions.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label className="stack">
            <span>Algorithm</span>
            <select
              value={preference.algorithm || 'hybrid'}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  algorithm: event.target.value as 'collaborative' | 'content_based' | 'hybrid'
                }))
              }
            >
              <option value="hybrid">Hybrid</option>
              <option value="collaborative">Collaborative</option>
              <option value="content_based">Content-based</option>
            </select>
          </label>

          <label className="stack">
            <span>Diversity ({preference.diversity.toFixed(2)})</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={preference.diversity}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  diversity: Number(event.target.value)
                }))
              }
            />
          </label>

          <label className="stack">
            <span>Recency bias ({preference.recency_bias.toFixed(2)})</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={preference.recency_bias}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  recency_bias: Number(event.target.value)
                }))
              }
            />
          </label>

          <label className="stack">
            <span>Max items per category</span>
            <input
              type="number"
              min={1}
              max={10}
              value={preference.maxPerCategory}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  maxPerCategory: Number(event.target.value)
                }))
              }
            />
          </label>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={preference.excludeViewed}
              onChange={(event) =>
                setPreference((current) => ({
                  ...current,
                  excludeViewed: event.target.checked
                }))
              }
            />
            Exclude viewed items
          </label>
        </div>

        <div className="row">
          <button onClick={() => void onSavePreferences()} disabled={savingPreference}>
            {savingPreference ? 'Saving…' : 'Save preferences'}
          </button>
          <button
            className="secondary"
            onClick={() => {
              setPreference(EMPTY_PREFERENCE);
            }}
            disabled={savingPreference}
          >
            Reset
          </button>
        </div>
      </section>

      <section className="card">
        <div className="section-header">
          <h2>Catalog</h2>
          <span className="badge">{products.length} products</span>
        </div>
        {loading ? (
          <div className="state">Loading products…</div>
        ) : (
          <div className="grid">
            {products.map((product) => (
              <article key={product.product_id} className="card nested-card">
                <strong>{product.name}</strong>
                <p className="muted">${product.price.toFixed(2)} · stock {product.stock_quantity}</p>
                <p>{product.description || 'No description provided.'}</p>
                <button onClick={() => void onAdd(product.product_id)} disabled={product.stock_quantity === 0}>
                  {product.stock_quantity === 0 ? 'Out of stock' : 'Add to cart'}
                </button>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <div className="section-header">
          <h2>Cart</h2>
          <span className="badge">{cart?.items.length || 0} items</span>
        </div>
        {!cart ? (
          <div className="state">No cart yet for this user.</div>
        ) : (
          <ul className="list">
            {cart.items.map((item) => (
              <li key={item.product_id}>
                Product #{item.product_id} × {item.quantity}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

function flattenCategories(categories: Category[]): string[] {
  const names = new Set<string>();

  const walk = (rows: Category[]) => {
    rows.forEach((category) => {
      names.add(category.name);
      if (category.sub_categories?.length) {
        walk(category.sub_categories);
      }
    });
  };

  walk(categories);
  return Array.from(names).sort((left, right) => left.localeCompare(right));
}

function createEventId(action: string, userId: string, productId: number): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${action}-${userId}-${productId}-${crypto.randomUUID()}`;
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const buffer = new Uint32Array(4);
    crypto.getRandomValues(buffer);
    return `${action}-${userId}-${productId}-${Array.from(buffer, (value) => value.toString(16)).join('')}`;
  }
  return `${action}-${userId}-${productId}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
