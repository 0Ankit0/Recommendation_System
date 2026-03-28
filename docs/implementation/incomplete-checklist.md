# Simple implementation checklist

This checklist captures items that were incomplete and are now implemented.

- [x] Add missing auth endpoints: `POST /api/auth/register` and `POST /api/auth/login`.
- [x] Enforce admin-only write access for catalog creation endpoints (`/api/categories`, `/api/products`).
- [x] Enforce authentication on protected cart mutation endpoint (`/api/cart/add`).
- [x] Keep Python 3.10 compatibility for UTC timestamp helpers in models and security utilities.
- [x] Validate implementation with automated tests.
