'use client';

import { useEffect, useState } from 'react';
import { addToCart, fetchCart, fetchCategories, fetchProducts } from '@/components/api';

const DEMO_USER = 'demo-user';

export default function HomePage() {
  const [categories, setCategories] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<any | null>(null);

  useEffect(() => {
    (async () => {
      setCategories(await fetchCategories());
      setProducts(await fetchProducts());
      setCart(await fetchCart(DEMO_USER));
    })();
  }, []);

  const onAdd = async (productId: number) => {
    await addToCart(DEMO_USER, productId, 1);
    setCart(await fetchCart(DEMO_USER));
  };

  return (
    <main>
      <h1>Recommendation System Migration Demo</h1>

      <section className="card">
        <h2>Categories</h2>
        <div className="grid">
          {categories.map((c) => (
            <div key={c.id}>
              <strong>{c.name}</strong>
              <div>{c.sub_categories?.length || 0} subcategories</div>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Products</h2>
        <div className="grid">
          {products.map((p) => (
            <div key={p.product_id} className="card">
              <strong>{p.name}</strong>
              <p>${p.price}</p>
              <button onClick={() => onAdd(p.product_id)}>Add to cart</button>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Cart ({DEMO_USER})</h2>
        {!cart ? (
          <div>No cart yet.</div>
        ) : (
          <ul>
            {cart.items.map((item: any) => (
              <li key={item.product_id}>Product #{item.product_id} × {item.quantity}</li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
