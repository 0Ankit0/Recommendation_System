# Sequence Diagram - Smart Recommendation Engine

## SD-01: Generate Recommendations (Internal)

```mermaid
sequenceDiagram
    participant API as RecommendationAPI
    participant FE as FeatureEngineer
    participant FS as FeatureStore
    participant PS as PredictionService
    participant Model as ML Model
    participant Cache as Redis
    
    API->>+FE: getUserFeatures(userId)
    FE->>+FS: query(userId)
    FS-->>-FE: features
    FE-->>-API: userFeatures
    
    API->>+FS: getCandidateItems(filters)
    FS-->>-API: itemIds[]
    
    API->>+PS: predict(userId, itemIds)
    PS->>+Cache: get(cacheKey)
    Cache-->>-PS: null
    
    PS->>+Model: inference(userFeatures, itemFeatures)
    Model-->>-PS: scores[]
    
    PS->>Cache: set(cacheKey, scores, TTL)
    PS-->>-API: predictions[]
    
    API-->>API: rankAndFilter()
    API-->>API: generateExplanations()
```

## SD-02: Model Training Pipeline

```mermaid
sequenceDiagram
    participant MT as ModelTrainer
    participant FS as FeatureStore
    participant Model as RecommenderModel
    participant ML as MLflowClient
    participant Registry as ModelRegistry
    
    MT->>MT: validateConfig()
    MT->>+FS: getTrainingData(dateRange)
    FS-->>-MT: interactions, features
    
    MT->>MT: splitData(train, valid, test)
    
    loop For each hyperparameter configuration
        MT->>+Model: train(trainData, config)
        Model-->>-MT: trainedModel
        
        MT->>+Model: evaluate(validData)
        Model-->>-MT: validMetrics
        
        MT->>+ML: logMetrics(validMetrics)
        ML-->>-MT: runId
    end
    
    MT->>MT: selectBestModel()
    MT->>+Model: evaluateOnTest()
    Model-->>-MT: testMetrics
    
    MT->>+Registry: saveModel(model, metadata)
    Registry-->>-MT: modelId
```

## SD-03: A/B Test Execution

```mermaid
sequenceDiagram
    participant User
    participant API as RecommendationAPI
    participant EXP as ExperimentManager
    participant MA as ModelA (Control)
    participant MB as ModelB (Variant)
    participant Tracker as MetricsTracker
    
    User->>+API: getRecommendations(userId)
    API->>+EXP: assignUserToGroup(userId, experimentId)
    EXP-->>-API: group

 = "control"
    
    alt Control Group
        API->>+MA: predict(userId)
        MA-->>-API: predictions
    else Variant Group
        API->>+MB: predict(userId)
        MB-->>-API: predictions
    end
    
    API-->>-User: recommendations[]
    
    Note over User: User interacts with recommendations
    
    User->>API: trackInteraction(userId, itemId, click)
    API->>Tracker: recordMetric(experimentId, group, metric)
```
