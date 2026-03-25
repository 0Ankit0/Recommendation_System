# Code Guidelines - Smart Recommendation Engine

## Python Project Structure

```
recommendation-engine/
├── src/
│   ├── api/                    # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── recommendation.py
│   │   ├── events.py
│   │   └── models.py
│   ├── ml/                     # ML models
│   │   ├── __init__.py
│   │   ├── base_recommender.py
│   │   ├── collaborative_filtering.py
│   │   ├── content_based.py
│   │   └── hybrid.py
│   ├── features/               # Feature engineering
│   │   ├── __init__.py
│   │   ├── user_features.py
│   │   └── item_features.py
│   ├── training/               # Training pipeline
│   │   ├── __init__.py
│   │   ├── trainer.py
│   │   └── evaluator.py
│   ├── serving/                # Model inference
│   │   ├── __init__.py
│   │   └── predictor.py
│   └── utils/
├── notebooks/                  # Jupyter experiments
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Base Recommender Class

```python
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class BaseRecommender(ABC):
    """Abstract base class for all recommendation algorithms"""
    
    def __init__(self, config: dict):
        self.config = config
        self.model = None
        
    @abstractmethod
    def train(self, interactions: pd.DataFrame, 
              user_features: pd.DataFrame,
              item_features: pd.DataFrame):
        """Train the recommendation model"""
        pass
        
    @abstractmethod
    def predict(self, user_id: str, 
                item_ids: list[str], 
                top_k: int = 10) -> list[tuple]:
        """Generate top-k recommendations for a user"""
        pass
        
    def save(self, path: str):
        """Save model to disk"""
        import joblib
        joblib.dump(self.model, path)
        
    def load(self, path: str):
        """Load model from disk"""
        import joblib
        self.model = joblib.load(path)
```

## Collaborative Filtering Example

```python
from sklearn.decomposition import TruncatedSVD

class CollaborativeFilteringRecommender(BaseRecommender):
    def __init__(self, config: dict):
        super().__init__(config)
        self.n_factors = config.get('n_factors', 50)
        self.model = TruncatedSVD(n_components=self.n_factors)
        
    def train(self, interactions, user_features=None, item_features=None):
        # Create user-item matrix
        user_item_matrix = interactions.pivot(
            index='user_id', 
            columns='item_id', 
            values='value'
        ).fillna(0)
        
        # Train matrix factorization
        self.model.fit(user_item_matrix)
        self.user_item_matrix = user_item_matrix
        
    def predict(self, user_id, item_ids, top_k=10):
        user_idx = self.user_item_matrix.index.get_loc(user_id)
        user_vector = self.model.transform(
            self.user_item_matrix.iloc[user_idx:user_idx+1]
        )
        
        # Compute scores
        scores = {}
        for item_id in item_ids:
            item_idx = self.user_item_matrix.columns.get_loc(item_id)
            item_vector = self.model.components_[:, item_idx]
            score = np.dot(user_vector, item_vector)[0]
            scores[item_id] = score
            
        # Return top-k
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
```

## FastAPI Endpoint

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class RecommendationRequest(BaseModel):
    user_id: str
    limit: int = 10
    algorithm: str = "hybrid"

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    try:
        # Load model
        recommender = load_recommender(request.algorithm)
        
        # Get candidate items
        candidate_items = get_candidate_items(request.user_id)
        
        # Generate predictions
        recommendations = recommender.predict(
            request.user_id,
            candidate_items,
            top_k=request.limit
        )
        
        return {
            "user_id": request.user_id,
            "recommendations": [
                {"item_id": item_id, "score": score}
                for item_id, score in recommendations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Dependencies

```txt
# Core ML
scikit-learn>=1.0.0
pandas>=1.3.0
numpy>=1.21.0

# Deep Learning (optional)
tensorflow>=2.8.0
# OR
torch>=1.11.0

# API
fastapi>=0.95.0
uv icorn>=0.21.0
pydantic>=1.10.0

# ML Infrastructure
mlflow>=2.0.0
feast>=0.25.0

# Data Processing
pyarrow>=10.0.0
```
