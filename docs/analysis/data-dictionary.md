# Data Dictionary - Smart Recommendation Engine

## Core Entities

### User
- **id**: UUID
- **segments**: array
- **preferences**: json

### Item
- **id**: UUID
- **type**: product | job | content | course
- **attributes**: json

### Interaction
- **id**: UUID
- **userId**: UUID
- **itemId**: UUID
- **action**: view | click | like | purchase | save
- **timestamp**: ISO 8601

### FeatureVector
- **id**: UUID
- **entityType**: user | item
- **vector**: array<float>
- **version**: string

### Recommendation
- **id**: UUID
- **userId**: UUID
- **items**: array
- **modelVersion**: string
- **generatedAt**: ISO 8601