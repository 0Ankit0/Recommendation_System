# ERD / Database Schema - Smart Recommendation Engine

```mermaid
erDiagram
    users ||--o{ interactions : performs
    users ||--o{ preferences : has
    items ||--o{ interactions : receives
    items ||--o{ features : has
    ml_models ||--o{ predictions : generates
    experiments ||--o{ model_variants : contains
    
    users {
        uuid id PK
        json demographics
        timestamp created_at
    }
    
    items {
        uuid id PK
        string type
        json metadata
        timestamp created_at
    }
    
    interactions {
        uuid id PK
        uuid user_id FK
        uuid item_id FK
        string action_type
        float value
        timestamp timestamp
        json context
    }
    
    features {
        uuid id PK
        uuid entity_id FK
        string entity_type
        string feature_name
        float value
        timestamp computed_at
    }
    
    ml_models {
        uuid id PK
        string algorithm
        string version
        json hyperparameters
        json metrics
        string status
        timestamp trained_at
    }
    
    predictions {
        uuid user_id FK
        uuid item_id FK
        uuid model_id FK
        float score
        json explanation
        timestamp generated_at
    }
    
    experiments {
        uuid id PK
        string name
        string status
        json config
        timestamp started_at
        timestamp ended_at
    }
    
    model_variants {
        uuid id PK
        uuid experiment_id FK
        uuid model_id FK
        float traffic_percent
        json metrics
    }
    
    preferences {
        uuid user_id PK,FK
        string preference_key PK
        json preference_value
    }
```

## Table Definitions

### interactions
```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    item_id UUID NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'view', 'click', 'purchase', 'like'
    value FLOAT DEFAULT 1.0,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    context JSONB,  -- device, session, etc.
    INDEX idx_user_time (user_id, timestamp),
    INDEX idx_item_time (item_id, timestamp)
);
```

### ml_models
```sql
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm VARCHAR(100) NOT NULL,  -- 'collaborative_filtering', 'content_based', etc.
    version VARCHAR(50) NOT NULL,
    hyperparameters JSONB,
    metrics JSONB,  -- precision, recall, NDCG, etc.
    status VARCHAR(20) DEFAULT 'training',  -- training, registered, production, deprecated
    trained_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(algorithm, version)
);
```

### predictions (Materialized for caching)
```sql
CREATE TABLE predictions (
    user_id UUID NOT NULL,
    item_id UUID NOT NULL,
    model_id UUID NOT NULL,
    score FLOAT NOT NULL,
    explanation JSONB,
    generated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, item_id, model_id),
    INDEX idx_user_score (user_id, score DESC)
);
```

## Enum Definitions

| Enum | Values |
|------|--------|
| action_type | view, click, purchase, like, save, share |
| model_status | training, registered, staging, production, deprecated |
| experiment_status | draft, running, analyzing, concluded |
