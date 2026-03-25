# Business Rules - Smart Recommendation Engine

## Ranking Rules
- Exclude items the user has already purchased unless re-order is enabled.
- Diversity constraint: no more than 3 items from the same category in top 10.

## Cold Start Rules
- New users receive popular items until 5 interactions are recorded.
- New items require a minimum metadata completeness score before serving.

## Safety & Fairness
- Remove items flagged by policy checks from ranking.
- Bias metrics must remain within configured thresholds.