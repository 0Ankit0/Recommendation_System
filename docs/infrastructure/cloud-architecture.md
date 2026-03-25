# Cloud Architecture - Smart Recommendation Engine

## AWS Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Compute"
            ECS[ECS Fargate<br/>API & Workers]
            SAGEMAKER[SageMaker<br/>Model Training]
        end
        
        subgraph "ML Services"
            SAGEMAKER_SERVE[SageMaker Endpoints<br/>Model Serving]
            FEATURE_STORE[SageMaker Feature Store]
        end
        
        subgraph "Data"
            RDS[(RDS PostgreSQL)]
            ELASTICACHE[(ElastiCache Redis)]
            MSK[MSK Kafka]
            S3[S3 Buckets]
        end
        
        subgraph "Monitoring"
            CLOUDWATCH[CloudWatch]
            XRAY[X-Ray]
        end
    end
    
    ALB[Application LB] --> ECS
    ECS --> SAGEMAKER_SERVE
    ECS --> FEATURE_STORE
    ECS --> RDS
    ECS --> ELASTICACHE
    
    SAGEMAKER --> FEATURE_STORE
    SAGEMAKER --> S3
    
    MSK --> ECS
    
    ECS --> CLOUDWATCH
    ECS --> XRAY
```

## GCP Architecture

```mermaid
graph TB
    subgraph "Google Cloud"
        subgraph "Compute"
            GKE[GKE<br/>Kubernetes]
            VERTEX_TRAIN[Vertex AI Training]
        end
        
        subgraph "ML Services"
            VERTEX_PRED[Vertex AI Prediction]
            FEAST[Feast on GKE]
        end
        
        subgraph "Data"
            CLOUD_SQL[(Cloud SQL)]
            MEMORYSTORE[(Memorystore)]
            PUB_SUB[Pub/Sub]
            GCS[Cloud Storage]
        end
    end
    
    LB[Cloud Load Balancing] --> GKE
    GKE --> VERTEX_PRED
    GKE --> FEAST
    GKE --> CLOUD_SQL
    GKE --> MEMORYSTORE
```

## Provider Mapping

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Container Runtime | ECS/EKS | GKE | AKS |
| Model Training | SageMaker | Vertex AI | Azure ML |
| Model Serving | SageMaker Endpoints | Vertex AI Prediction | Azure ML Endpoints |
| Feature Store | SageMaker Feature Store | Feast on GKE | Azure ML Feature Store |
| Database | RDS PostgreSQL | Cloud SQL | Azure PostgreSQL |
| Cache | ElastiCache | Memorystore | Azure Cache |
| Message Queue | MSK/SQS | Pub/Sub | Event Hubs |
| Vector DB | Self-managed | Self-managed | Self-managed |
| ML Registry | Self-managed MLflow | Self-managed MLflow | Azure ML Registry |

## Cost Estimation (AWS)

| Tier | Monthly Cost | Specs |
|------|--------------|-------|
| **Starter** | ~$500 | 2 API instances, t3.medium, basic ML |
| **Growth** | ~$2000 | Auto-scaling, r5.large, GPU training |
| **Enterprise** | ~$8000+ | Multi-region, dedicated GPU, HA |
