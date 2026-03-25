# Edge Cases - API & UI

### 5.1. Stale Recommendations
* **Scenario**: Cached recommendations are outdated.
* **Impact**: Users see irrelevant items.
* **Solution**:
    * **TTL**: Short cache TTL for fast-moving catalogs.
    * **Refresh**: Force refresh after key interactions.

### 5.2. Pagination Drift
* **Scenario**: Items change between pages.
* **Impact**: Duplicates or missing items.
* **Solution**:
    * **Pagination**: Cursor-based pagination with stable ranking.
    * **Consistency**: Lock ranking snapshot for a session.