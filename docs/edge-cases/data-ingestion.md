# Edge Cases - Data Ingestion

### 1.1. Event Duplication
* **Scenario**: The same interaction event is ingested multiple times.
* **Impact**: Inflated interaction counts and biased recommendations.
* **Solution**:
    * **Idempotency**: Deduplicate using event IDs and time windows.
    * **Monitoring**: Track duplication rates per source.

### 1.2. Out-of-Order Events
* **Scenario**: Events arrive late or out of sequence.
* **Impact**: Incorrect session features and recency signals.
* **Solution**:
    * **Processing**: Use event-time ordering with watermarks.
    * **Policy**: Drop or downweight events beyond lateness threshold.

### 1.3. Missing User or Item IDs
* **Scenario**: Events are missing user or item identifiers.
* **Impact**: Feature pipeline failures.
* **Solution**:
    * **Validation**: Reject invalid events and log source errors.
    * **Fallback**: Use anonymous user profiles when allowed.