# Sync Pipeline - Staff Assignment

## Problem statement (Provided)

1. Outreach's sync team is responsible for bidirectional data sync between multiple services. For the sake of this assignment - the sync process is limited into 2 types of services - 
   1. Internal services (full access to data, services)
   2. External services (interaction via REST apis)
2. This is a record-to-record synchronization service signifying each record translates to a actionable item for the sync service.
3. The system handles CRUD operations between both systems.
4. The system must handle over 300 million synchronization requests daily.
5. The system must have near real time latency.
6. System should have 99.9% availability.
7. External APIs cannot support unlimited requests. 
8. Some data transformations are required to map between internal and external schemas. 
9. The system must support multiple CRM providers. 
10. Synchronization must occur record-by-record. 
11. Input/output should be validated against predefined schemas. 
12. Data must be transformed into/from the specific object models before being processed.
13. Sync actions (CRUD) are determined by pre-configured rules or triggers

## Sub-Problem Picked

As mentioned in the assignment, only a part of the whole system needs to be designed and implemented.

There are multiple sub problems to this service from a very high level.

1. Internal to External data sync.
2. External to internal data sync.
3. Consistency issues and resolution.
4. Data transformer layer.
5. Trigger rule engine, etc.

I am choosing Internal to External data sync process for this assignment. The following document contains the HighLevelDesign (design decisions, tradeoffs, design diagrams, etc.)

## Requirements

### Functional Requirements

1. CRUD synchronization between two systems : The service synchronizes Create, Update, and Delete operations between an internal system (System A, fully owned) and external systems (System B, CRMs accessible only via API). READ is out of scope for this assignment. Only internal to external synchronization is in scope of this assignment.
2. Multi-tenant : The service handles many tenants concurrently. Each tenant's data, rate limits are logically isolated from other tenants.
3. Multiple CRM provider support :  The service integrates with multiple external CRM providers (e.g., Salesforce, HubSpot). Provider-specific differences (schema, rate limits, response modes, idempotency primitives) are encapsulated behind pluggable interfaces so new providers can be added without core changes.
4. Pluggable schema transformation layer : Data is transformed between internal and external schemas before being written. The transformation layer is pluggable per-provider and per-direction.
5. Record-level ordering : Operations on the same record must be applied to the destination in the order they occurred at the source. Operations on different records may be applied in parallel.
6. Per-tenant rate limiting : External API rate limits are enforced per-tenant, per-provider. Without per-tenant scoping, one hot tenant would consume the shared budget and starve quieter tenants.
7. Idempotent delivery : Each sync operation is delivered exactly once in effect, even across retries, transient failures, and crash recovery. Duplicate submissions must not cause duplicate writes on the destination.
8. Input/output schema validation : All events entering the pipeline and all payloads sent to external systems are validated against predefined schemas. Validation failures are non-retryable.
9. One-to-many destination routing : A single record change in the source can be configured to sync to multiple external CRMs, each with its own provider, schema transformation, and rate limit. Each destination is an independent delivery.

### Non-Functional Requirements

1. Throughput: 300M events/day with 10× burst absorption. Steady-state average ~3,500 events/sec. Traffic is bursty, not smoothed — for this assignment, assume a 10× burst factor (~35,000 events/sec peak). The pipeline must absorb and smooth these peaks while respecting downstream rate limits; it cannot propagate burstiness directly to external APIs.
2. Tiered latency - "Near real-time" - I have classified it based on data types being synced. Any tenant can have at least one or all data types.
   1. Critical: p95 < 2s
   2. Standard: p95 < 5s
   3. Background: p95 < 15s
   For the sake of simplicity i have implemented considering single data type. But designed for all 3.
3. Availability: 99.9%. Availability is tracked independently per tenant and per provider.
4. Failure isolation - A single failing tenant, degraded provider, or malformed record must not degrade service for other tenants or providers. 


### Assumptions
1. Upstream system exists and is multi-tenant - A pre-existing internal system handles multi-tenant data operations. This sync service consumes change events from it; it does not replace it.
2. Trigger/rule engine is out of scope - The logic that decides which state changes trigger a sync (and to which CRMs) lives upstream, outside this service. Those rules are assumed to be configurable and extensible, but the engine itself is not part of this assignment.
3. Events arriving at this service are pre-decided sync intents. By the time an event reaches this pipeline, the upstream trigger engine has already decided it must be delivered. The pipeline does not filter, deduplicate, or re-evaluate rules — it delivers.
4. READ operations are not synced. The problem statement lists READ as an operation type, but in practice READ is rarely a sync intent — it is a side-effect of reconciliation. Scoped out for simplicity.
5. Rate limits vary per tenant. Each (tenant, provider) pair has its own rate-limit budget. Enterprise tenants may negotiate higher limits than the provider default; config supports per-tenant overrides.
6. Conflict resolution is out of scope. When a write to an external system would conflict with concurrent changes (version mismatch), this service rejects the write and surfaces the conflict. Deciding who wins is handled by an upstream reconciliation service.
7. Upstream ordering is preserved at the source. The internal system emits events for the same record in the order operations occurred.
8. Authentication and credential management are out of scope. External API credentials are assumed provided via a CredentialProvider abstraction.

## Component Diagram

[ToBeReplaced](IMG_8218.HEIC)


## Sync Service

[ToBeReplaced](IMG_8219.HEIC)

### Service Invocation (Push vs Pull)

There are 2 ways to invoke sync service for any record - either internal systems push this data to service or sync service pulls the record to sync it.

There is an explicit requirement that all the events will not be synced and based on pre configured rules - a rule engine will decide which event will be synced to which external system.

Now lets compare the pros and cons of both push vs pull : 
#### Push : 
1. The sync service should be able to consume the messages at the same rate as produced. If consumer throughput is breached - producer need to store messages, maintain order and retry them.
2. If sync service is not available - it is the responsibility of consumer to store messages, maintain order and retry them.

#### Pull : 
1. The consumer needs to store the message at their end before they are being pulled by sync service.
2. Extra latency introduced due to the time gap between message is produced vs pulled by sync service.

Pull is the selected method here as it makes consumer more self reliant and removes dependency from sync service.
So internal systems will write records / messages in order into a durable log.

### Durable log (DB/ FIFO SQS/ Kaka)

Internal system after filtering the message using rules , need to pass the messages to sync service while maintaing order. 
Thus, a system where sync service exposes an api for receiving messages while persisting messages at their end will not work as order will not be guaranteed.

We need a reliable and durable way to pass these messages. Let's compare the 3 available options:

#### DB -
1. Schema limitation introduced.
2. Write / read will have similar scale - maintaining 35000 events/sec on db can be challenging.
3. (Pros) Audit history / status of records can be maintained using db.

#### FIFO Queues (SQS) - 
1. Normal FIFO SQS has 300 events/sec rate limit, but in some regions it can be increased (these regions will contribute to latency).
2. Creating 3 new queues for each tenant and maintaining them will be hard on scale.
3. No retry support.
4. (Pros) Message Delay and DLQ support out of the box.

#### Kafka
1. Partitions are ordered.
2. Durable, replayable.
3. Adding new tenants will not hurt.
4. No limitation due to rate limits. (enforced by internal team so can be changed per usage)

To maintain the scale and growing demand, kafka is selected otherwise FIFO SQS can be leveraged.

#### Kafka config
1. Separate topic per tenant : 
   1. Each tenant will have N partitions. 
   2. record_id will be hashed to a partition.
   3. Implementation is simple and clean - also each tenant will be independent completely.
   4. Can cause issue as brokers can handle 10000 partitions gracefully.
2. tenant_id#record_id as partition key :
   1. Data of tenants are not isolated.
   2. One hot partition (due to one tenant) can delay messages of other tenants.
   3. True parallelism for tenants cannot be achieved. Scaling consumers of a partition will be tough.
   4. Can be solved by adding tiered routing and another layer of queue sets.

I am preferring option 1 due to mentioned reasons.

### Consumers

Each consumer will perform following steps : 
1. Read from partition.
2. Validate the record schema (FR) as per the metadata rules.
3. Transform message into external system structure using the transformer service.
4. A single record from internal systems can be sent to more than one external system.
5. Send to external system queue.

### External system queue consumers
These consumers will be sending data to external systems and need to maintain distributed rate limiting, circuit breaker.
These also need to handle retry mechanism in case any system returns failure.

1. Each consumer will read the message.
2. Check circuit breaker
3. Check rate limiter
4. Send message to external system
5. Store the ack back in a persistent store.

