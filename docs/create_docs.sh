#!/bin/bash

# Analysis Phase Files
cat > "analysis/use-case-descriptions.md" << 'ANALYSIS_UCD'
# Use Case Descriptions - Smart Recommendation Engine

## UC-01: View Recommendations
**Actor**: End User  
**Description**: User receives personalized item recommendations

**Main Flow**:
1. User opens application/page
2. System retrieves user history and preferences
3. System generates recommendations using ML models
4. System displays recommended items
5. User browses recommendations

**Success**: Relevant recommendations displayed < 100ms

---

## UC-02: Train ML Model
**Actor**: Data Scientist  
**Description**: Train new recommendation model on historical data

**Main Flow**:
1. Data Scientist selects algorithm (collaborative filtering, content-based, hybrid)
2. Data Scientist configures hyperparameters
3. System loads training data from feature store
4. System trains model (batch process)
5. System evaluates on test set
6. Data Scientist reviews metrics
7. System saves model to registry

**Success**: Model trained and registered with performance metrics
ANALYSIS_UCD

# High-Level Design Files
cat > "../high-level-design/domain-model.md" << 'HLD_DOMAIN'
# Domain Model - Smart Recommendation Engine

```mermaid
erDiagram
    USER ||--o{ INTERACTION : performs
    USER ||--o{ PREFERENCE : has
    USER {
        string userId PK
        json demographics
        json preferences
    }
    
    ITEM ||--o{ INTERACTION : receives
    ITEM ||--o{ FEATURE : has
    ITEM {
        string itemId PK
        string type
        json metadata
        json features
    }
    
    INTERACTION {
        string interactionId PK
        string userId FK
        string itemId FK
        string actionType
        timestamp timestamp
        json context
    }
    
    ML_MODEL ||--o{ PREDICTION : generates
    ML_MODEL {
        string modelId PK
        string algorithm
        string version
        json hyperparameters
        json metrics
    }
    
    PREDICTION {
        string userId FK
        string itemId FK
        float score
        json explanation
    }
```

**Key Entities**:
- **User**: Person receiving recommendations
- **Item**: Entity being recommended
- **Interaction**: User action (view, click, purchase)
- **ML Model**: Trained recommendation algorithm
- **Prediction**: Recommendation score for user-item pair
HLD_DOMAIN

# Detailed Design Files
cat > "../detailed-design/api-design.md" << 'API_DESIGN'
# API Design - Smart Recommendation Engine

## Base URL
`https://api.example.com/v1`

---

## Track User Action
**POST** `/events`

**Request**:
```json
{
  "userId": "user123",
  "itemId": "item456",
  "actionType": "view",
  "timestamp": "2024-01-20T10:00:00Z",
  "context": {
    "device": "mobile",
    "session": "sess789"
  }
}
```

**Response**: `202 Accepted`

---

## Get Recommendations
**GET** `/recommendations/{userId}`

**Query Params**:
- `algorithm`: collaborative | content_based | hybrid
- `limit`: number of items (default: 10)
- `explain`: boolean (include explanations)

**Response**:
```json
{
  "userId": "user123",
  "recommendations": [
    {
      "itemId": "item456",
      "score": 0.95,
      "rank": 1,
      "explanation": "Based on your recent views"
    }
  ],
  "metadata": {
    "algorithm": "hybrid",
    "modelVersion": "v1.2.3"
  }
}
```

---

## Train Model
**POST** `/models/train`

**Request**:
```json
{
  "algorithm": "collaborative_filtering",
  "hyperparameters": {
    "n_factors": 50,
    "epochs": 20
  },
  "dataRange": {
    "start": "2024-01-01",
    "end": "2024-01-20"
  }
}
```

**Response**:
```json
{
  "jobId": "train-job-123",
  "status": "queued"
}
```
API_DESIGN

# Infrastructure Files  
cat > "../infrastructure/deployment-diagram.md" << 'INFRA_DEPLOY'
# Deployment Diagram - Smart Recommendation Engine

```mermaid
graph TB
    subgraph "Application Tier"
        API[API Service<br/>FastAPI/Flask]
        WORKER[Training Worker<br/>Python]
    end
    
    subgraph "ML Infrastructure"
        FEATURE[Feature Store<br/>Feast/Tecton]
        REGISTRY[Model Registry<br/>MLflow]
        SERVING[Model Serving<br/>TF Serving/TorchServe]
    end
    
    subgraph "Data Tier"
        DB[(PostgreSQL<br/>User/Item/Interaction)]
        VECTOR[(Vector DB<br/>Milvus/Pinecone)]
        STREAM[Event Stream<br/>Kafka]
    end
    
    API --> FEATURE
    API --> SERVING
    API --> DB
    API --> STREAM
    
    WORKER --> FEATURE
    WORKER --> REGISTRY
    WORKER --> DB
    
    SERVING --> REGISTRY
```
INFRA_DEPLOY

# Implementation Files
cat > "../implementation/code-guidelines.md" << 'IMPL_CODE'
# Code Guidelines - Smart Recommendation Engine

## Python Project Structure

```
recommendation-engine/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── models/           # ML model classes
│   ├── features/         # Feature engineering
│   ├── training/         # Training pipeline
│   ├── serving/          # Model inference
│   └── utils/
├── notebooks/            # Jupyter for experiments
├── tests/
├── requirements.txt
└── pyproject.toml
```

## ML Model Template

```python
class RecommendationModel:
    def __init__(self, algorithm='collaborative_filtering'):
        self.algorithm = algorithm
        self.model = None
        
    def train(self, interactions_df, features_df):
        """Train model on historical data"""
        pass
        
    def predict(self, user_id, item_ids, top_k=10):
        """Generate recommendations"""
        pass
        
    def explain(self, user_id, item_id):
        """Explain why item recommended"""
        pass
```

## Dependencies
- **ML**: scikit-learn, pandas, numpy
- **Deep Learning** (optional): tensorflow, pytorch
- **API**: fastapi, pydantic
- **Feature Store**: feast
- **Model Registry**: mlflow
IMPL_CODE

echo "Analysis, High-Level, Detailed, Infrastructure, and Implementation files created"
ANALYSIS_UCD
