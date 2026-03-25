# Event Catalog - Smart Recommendation Engine

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| interaction.recorded | API | Feature Pipeline | User action captured |
| features.updated | Feature Pipeline | Model Training | Feature store updated |
| model.trained | Training Pipeline | Model Registry | Model training completed |
| model.deployed | Model Registry | Serving Layer | Model version activated |
| recommendation.generated | Serving Layer | Analytics | Recommendations served |