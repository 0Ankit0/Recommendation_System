# Edge Cases - Ranking & Bias

### 4.1. Popularity Bias
* **Scenario**: Popular items dominate rankings, starving long-tail items.
* **Impact**: Reduced catalog exposure and user discovery.
* **Solution**:
    * **Diversification**: Enforce diversity constraints.
    * **Re-ranking**: Blend popularity with novelty signals.

### 4.2. Filter Bubble
* **Scenario**: Users repeatedly see similar items.
* **Impact**: Engagement stagnation.
* **Solution**:
    * **Exploration**: Inject exploratory items with controlled rate.
    * **Feedback**: Use negative feedback signals to diversify.

### 4.3. Sensitive Attribute Leakage
* **Scenario**: Recommendations infer sensitive attributes indirectly.
* **Impact**: Fairness and compliance risks.
* **Solution**:
    * **Policy**: Remove sensitive features and audit ranking outcomes.
    * **Monitoring**: Track fairness metrics.