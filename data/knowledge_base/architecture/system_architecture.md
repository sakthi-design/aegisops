# Production Core Banking & Payments Architecture

## Services Topology
- **Edge Layer:** Cloudflare CDN & WAF -> AWS ALB (`ingress-alb-prod`)
- **API Gateway:** Envoy Proxy / Kong Gateway (`api-gateway-service`)
  - Rate limiting: 10,000 req/sec
  - Timeout: 5000ms
  - Health check endpoint: `/healthz`
- **Authentication Service:** Auth0 + OAuth2 Token Verifier (`auth-service-v2`)
- **Checkout & Order Service:** Go microservice (`order-service`)
- **Payment Processing Engine:** Java Spring Boot (`payment-processor`)
  - Database: Aurora PostgreSQL Multi-AZ (`payments-db-primary`, `payments-db-replica-1`)
  - Connection Pool: HikariCP (Max connections: 100, min idle: 20, connection timeout: 3000ms)
  - Circuit Breaker: Resilience4j to 3rd-party banking rails (Stripe / Adyen)
- **Message Broker:** Apache Kafka Cluster (3 brokers, replication factor: 3)
  - Topics: `payment.initiated`, `payment.authorized`, `payment.failed`, `order.events`
- **Cache Cluster:** Redis Sentinel Cluster (`redis-session-cache`)

## Dependency Graph
`ingress-alb-prod` -> `api-gateway-service` -> `payment-processor` -> `payments-db-primary`
`payment-processor` -> `redis-session-cache`
`payment-processor` -> `Kafka Broker 1,2,3`
`payment-processor` -> `Stripe Payment Gateway (External)`
