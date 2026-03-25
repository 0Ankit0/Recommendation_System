# API Design - Smart Recommendation Engine

**Base URL**: `https://api.example.com/v1`  
**Auth**: Bearer Token

---

## Track User Action
**POST** `/events`

```json
{
  "userId": "user123",
  "itemId": "item456",
  "actionType": "view",
  "value": 1.0,
  "timestamp": "2024-01-20T10:00:00Z",
  "context": {"device": "mobile"}
}
```

**Response**: `202 Accepted`

---

## Get Recommendations
**GET** `/recommendations/{userId}`

**Query Params**:
- `algorithm`: collaborative | content_based | hybrid
- `limit`: int (default: 10)
- `explain`: boolean

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
  "metadata": {"algorithm": "hybrid", "modelVersion": "v1.2.3"}
}
```

---

## Set User Preferences
**PUT** `/users/{userId}/preferences`

```json
{
  "categories": ["tech", "sports"],
  "diversity": 0.7,
  "recency_bias": 0.3
}
```

---

## Train Model
**POST** `/models/train`

```json
{
  "algorithm": "collaborative_filtering",
  "hyperparameters": {"n_factors": 50, "epochs": 20},
  "dataRange": {"start": "2024-01-01", "end": "2024-01-20"}
}
```

**Response**:
```json
{
  "jobId": "train-job-123",
  "status": "queued"
}
```

---

## Get Model Metrics
**GET** `/models/{modelId}/metrics`

**Response**:
```json
{
  "modelId": "model-123",
  "metrics": {
    "precision@10": 0.25,
    "recall@10": 0.18,
    "ndcg@10": 0.42,
    "diversity": 0.75
  }
}
```

---

## Create A/B Experiment
**POST** `/experiments`

```json
{
  "name": "New CF Model Test",
  "controlModelId": "model-v1",
  "variantModelId": "model-v2",
  "trafficSplit": {" control": 0.9, "variant": 0.1},
  "metrics": ["ctr", "conversion_rate"]
}
```
