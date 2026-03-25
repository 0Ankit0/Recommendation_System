# Domain Model - Smart Recommendation Engine

```mermaid
erDiagram
    USER ||--o{ INTERACTION : performs
    USER ||--o{ PREFERENCE : has
    USER {
        string userId PK
        json demographics
        timestamp createdAt
    }
    
    ITEM ||--o{ INTERACTION : receives
    ITEM ||--o{ FEATURE : has
    ITEM {
        string itemId PK
        string type
        json metadata
        timestamp createdAt
    }
    
    INTERACTION {
        string interactionId PK
        string userId FK
        string itemId FK
        string actionType
        float value
        timestamp timestamp
        json context
    }
    
    FEATURE {
        string featureId PK
        string entityId FK
        string featureName
        float value
        timestamp computedAt
    }
    
    ML_MODEL ||--o{ PREDICTION : generates
    ML_MODEL {
        string modelId PK
        string algorithm
        string version
        json hyperparameters
        json metrics
        timestamp trainedAt
    }
    
    PREDICTION {
        string userId FK
        string itemId FK
        string modelId FK
        float score
        json explanation
        timestamp generatedAt
    }
    
    EXPERIMENT ||--o{ MODEL_VARIANT : contains
    EXPERIMENT {
        string experimentId PK
        string name
        string status
        json config
    }
    
    MODEL_VARIANT {
        string variantId PK
        string experimentId FK
        string modelId FK
        float trafficPercent
        json metrics
    }
```

**Domain Services**:
- **FeatureEngineering**: Extract and compute features from raw data
- **ModelTraining**: Train ML models on historical data
- **RecommendationGeneration**: Generate personalized recommendations
- **ExperimentManagement**: Run A/B tests
