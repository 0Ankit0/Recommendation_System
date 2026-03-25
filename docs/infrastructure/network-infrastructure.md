# Network / Infrastructure Diagram - Smart Recommendation Engine

```mermaid
graph TB
    subgraph "Public Subnet - 10.0.1.0/24"
        LB[Load Balancer]
        NAT[NAT Gateway]
    end
    
    subgraph "Private Subnet - App - 10.0.2.0/24"
        API1[API 10.0.2.10]
        API2[API 10.0.2.11]
        WORKER[Worker 10.0.2.20]
    end
    
    subgraph "Private Subnet - ML - 10.0.3.0/24"
        FEATURE[Feature Store 10.0.3.10]
        SERVING[Model Serving 10.0.3.20]
        VECTOR[Vector DB 10.0.3.30]
    end
    
    subgraph "Private Subnet - Data - 10.0.4.0/24"
        DB[(PostgreSQL 10.0.4.10)]
        REDIS[(Redis 10.0.4.20)]
        KAFKA[Kafka 10.0.4.30]
    end
    
    INTERNET((Internet)) --> LB
    LB --> API1
    LB --> API2
    
    API1 --> SERVING
    API1 --> FEATURE
    API1 --> DB
    API1 --> REDIS
    
    WORKER --> FEATURE
    WORKER --> DB
    WORKER --> KAFKA
    
    SERVING --> VECTOR
```

## Firewall Rules

| From | To | Port | Protocol | Purpose |
|------|-----|------|----------|---------|
| Internet | LB | 443 | HTTPS | API access |
| LB | API Servers | 8000 | HTTP | Internal routing |
| API Servers | ML Services | various | HTTP/gRPC | ML inference |
| API Servers | Data | 5432, 6379 | TCP | Database access |
| Workers | Feature Store | 6566 | gRPC | Feature retrieval |

**Security Zones**:
- **DMZ**: Load balancer
- **Application**: API servers, workers
- **ML**: Feature store, model serving
- **Data**: Databases, message queues
