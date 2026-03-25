# Edge Cases - Operations

### 7.1. Feature Store Outage
* **Scenario**: Feature store becomes unavailable.
* **Impact**: Recommendations degrade or fail.
* **Solution**:
    * **Fallback**: Use cached features or last-known-good vectors.
    * **Monitoring**: Alert on feature store latency.

### 7.2. A/B Test Contamination
* **Scenario**: Users switch between experiment variants.
* **Impact**: Invalid experiment results.
* **Solution**:
    * **Bucketing**: Stable user bucketing and sticky assignments.
    * **Audit**: Track experiment exposure logs.