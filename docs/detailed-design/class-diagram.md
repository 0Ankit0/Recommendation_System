# Class Diagram - Smart Recommendation Engine

## Python ML Classes

```mermaid
classDiagram
    class RecommendationEngine {
        -FeatureStore featureStore
        -ModelRegistry modelRegistry
        -ConfigManager config
        +getRecommendations(userId, limit) List~Item~
        +trackAction(userId, itemId, action)
        +explainRecommendation(userId, itemId) Explanation
    }
    
    class BaseRecommender {
        <<abstract>>
        #model Any
        #config Dict
        +train(interactions, features)
        +predict(userId, itemIds) List~float~
        +save(path)
        +load(path)
    }
    
    class CollaborativeFilteringRecommender {
        -n_factors int
        -algorithm str
        +train(interactions, features)
        +predict(userId, itemIds) List~float~
        -computeSimilarity() Matrix
    }
    
    class ContentBasedRecommender {
        -vectorizer TfidfVectorizer
        -similarity_metric str
        +train(interactions, features)
        +predict(userId, itemIds) List~float~
        -computeItemEmbeddings() Matrix
    }
    
    class HybridRecommender {
        -recommenders List~BaseRecommender~
        -weights List~float~
        +train(interactions, features)
        +predict(userId, itemIds) List~float~
        -ensemblePredictions() List~float~
    }
    
    class FeatureEngineer {
        -featureStore FeatureStore
        +extractUserFeatures(userId) Dict
        +extractItemFeatures(itemId) Dict
        +computeInteractionFeatures(interactions) DataFrame
        +normalizeFeatures(features) DataFrame
    }
    
    class ModelTrainer {
        -featureStore FeatureStore
        -mlflowClient MLflowClient
        +trainModel(config) TrainingResult
        +evaluateModel(model, testData) Metrics
        +hyperparameterTune(searchSpace) BestParams
    }
    
    class PredictionService {
        -modelCache Dict
        -predictionCache Redis
        +predict(userId, itemIds) List~Prediction~
        -loadModel(modelId) Model
        -cacheResult(key, value)
    }

    class PolicyEngine {
        +applyDiversity(rankedItems) List~Item~
        +applyFilters(userId, items) List~Item~
    }

    class DriftMonitor {
        +detect(featureStats) DriftReport
    }

    class BiasEvaluator {
        +evaluate(recommendations) BiasReport
    }
    
    BaseRecommender <|-- CollaborativeFilteringRecommender
    BaseRecommender <|-- ContentBasedRecommender
    BaseRecommender <|-- HybridRecommender
    RecommendationEngine --> BaseRecommender
    RecommendationEngine --> FeatureEngineer
    RecommendationEngine --> PolicyEngine
    ModelTrainer --> BaseRecommender
    PredictionService --> BaseRecommender
```

## Data Classes

```mermaid
classDiagram
    class User {
        +str userId
        +Dict demographics
        +List~str~ preferences
        +DateTime createdAt
    }
    
    class Item {
        +str itemId
        +str type
        +Dict metadata
        +Dict features
    }
    
    class Interaction {
        +str interactionId
        +str userId
        +str itemId
        +str actionType
        +float value
        +DateTime timestamp
        +Dict context
    }
    
    class Prediction {
        +str userId
        +str itemId
        +float score
        +int rank
        +str modelVersion
        +Dict explanation
    }
    
    class MLModel {
        +str modelId
        +str algorithm
        +str version
        +Dict hyperparameters
        +Dict metrics
        +DateTime trainedAt
    }
```

**Key Python Libraries**:
- scikit-learn: Traditional ML algorithms
- TensorFlow/PyTorch: Deep learning models
- pandas/numpy: Data manipulation
- MLflow: Experiment tracking
- Feast: Feature store
