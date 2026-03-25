# C4 Code Diagram - Smart Recommendation Engine

## Collaborative Filtering Module

```python
# collaborative_filtering.py

from abc import ABC
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from typing import List, Tuple

class BaseRecommender(ABC):
    """Base class for all recommenders"""
    def __init__(self, config: dict):
        self.config = config
        
    def train(self, data):
        pass
        
    def predict(self, user_id, item_ids):
        pass

class MatrixFactorizationRecommender(BaseRecommender):
    """SVD-based collaborative filtering"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.svd = TruncatedSVD(
            n_components=config.get('n_factors', 50)
        )
        self.user_factors = None
        self.item_factors = None
        
    def train(self, interactions: pd.DataFrame):
        # Create user-item matrix
        matrix = self._create_matrix(interactions)
        
        # Decompose
        self.user_factors = self.svd.fit_transform(matrix)
        self.item_factors = self.svd.components_.T
        
    def predict(self, user_id: str, 
                item_ids: List[str]) -> List[Tuple[str, float]]:
        user_vec = self._get_user_vector(user_id)
        
        scores = []
        for item_id in item_ids:
            item_vec = self._get_item_vector(item_id)
            score = np.dot(user_vec, item_vec)
            scores.append((item_id, score))
            
        return sorted(scores, key=lambda x: x[1], reverse=True)
```

## Feature Engineering Module

```python
# feature_engineer.py

import pandas as pd
from feast import FeatureStore

class FeatureEngineer:
    """Extract and compute ML features"""
    
    def __init__(self, feature_store_path: str):
        self.fs = FeatureStore(repo_path=feature_store_path)
        
    def get_user_features(self, user_id: str) -> pd.DataFrame:
        """Retrieve user features from feature store"""
        entity_rows = [{"user_id": user_id}]
        
        features = self.fs.get_online_features(
            features=[
                "user_stats:view_count_7d",
                "user_stats:avg_rating",
                "user_demographics:age_group"
            ],
            entity_rows=entity_rows
        ).to_df()
        
        return features
        
    def compute_interaction_features(
        self, 
        interactions: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute aggregate interaction features"""
        
        features = interactions.groupby('user_id').agg({
            'item_id': 'count',  # interaction_count
            'value': 'mean',     # avg_interaction_value
            'timestamp': 'max'   # last_interaction
        })
        
        return features
```

## Model Training Orchestrator

```python
# trainer.py

import mlflow
from typing import Dict

class ModelTrainer:
    """Orchestrate ML model training"""
    
    def __init__(self, mlflow_tracking_uri: str):
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        
    def train_model(
        self,
        recommender_class,
        config: Dict,
        train_data: pd.DataFrame,
        val_data: pd.DataFrame
    ):
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params(config)
            
            # Train model
            recommender = recommender_class(config)
            recommender.train(train_data)
            
            # Evaluate
            metrics = self._evaluate(recommender, val_data)
            mlflow.log_metrics(metrics)
            
            # Save model
            mlflow.sklearn.log_model(recommender.model, "model")
            
            return recommender
            
    def _evaluate(self, recommender, val_data):
        # Compute precision@k, recall@k, etc.
        return {
            "precision@10": 0.25,
            "recall@10": 0.18,
            "ndcg@10": 0.42
        }
```

**Module Interaction**:
1. **FeatureEngineer** extracts features from FeatureStore
2. **MatrixFactorizationRecommender** trains on features
3. **ModelTrainer** orchestrates training with MLflow
4. **PredictionService** serves trained models via API
