# ADR 002 — Why Kafka (Planned / Future)

| Field       | Value                          |
|-------------|-------------------------------|
| **Status**  | Proposed                       |
| **Date**    | 2026-09-01                     |
| **Author**  | Mohammad Saif                  |

---

## Context

The current ELT-Lakehouse pipeline runs in **batch mode**: a pool of synthetic
customers, products, sellers, and order data is generated on each run, written
to Parquet files, ingested through Bronze, validated in Silver, and aggregated
in Gold.

As the project evolves toward a production-realistic architecture, there is a
need for a **streaming ingestion layer** that:

1. Decouples data producers (the generators) from data consumers (Spark).
2. Provides a durable, replayable log so failed Silver runs can re-process from
   a known offset — without regenerating source data.
3. Supports back-pressure naturally: if Silver processing is slow, Kafka retains
   unconsumed messages.
4. Models how a real e-commerce platform would emit events (order placed, payment
   confirmed, review submitted, …) as they occur.

---

## Decision

**Apache Kafka** is the planned streaming backbone for the future streaming mode
of this pipeline.

```
Generators  ──► Kafka Topics  ──► Spark Structured Streaming  ──► Bronze Delta
              (one topic per entity)                            (micro-batch or
                                                                 continuous)
```

This ADR documents the **rationale** for choosing Kafka; actual implementation
is tracked separately and is not yet active in the codebase.

---

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Apache Pulsar** | Multi-tenancy, geo-replication | Smaller ecosystem; less Spark-native support |
| **AWS Kinesis** | Managed, tight AWS integration | Cloud-only; defeats local-dev goal |
| **Google Pub/Sub** | Managed, auto-scaling | Cloud-only |
| **RabbitMQ** | Lightweight, easy AMQP setup | Not a log; no replay; no offset management |
| **Apache Kafka** ✅ | Industry standard, replay, Spark Structured Streaming native, runs locally with KRaft | Requires running a broker (adds local infra complexity) |

---

## Consequences

### Positive
- Generators become stateless producers — they emit to a topic and stop; no
  file management required.
- Spark reads via `spark.readStream.format("kafka")` with exactly-once
  semantics using Delta Lake as the sink.
- Offset checkpointing means a crashed Silver job resumes from where it left
  off, not from the beginning.
- A local single-broker KRaft Kafka instance is sufficient for development.

### Negative / Trade-offs
- Adds operational complexity: Kafka broker must be running before the pipeline
  starts.
- Message serialisation format must be agreed upon (JSON vs Avro vs Protobuf).
  Avro with Schema Registry is preferred for schema evolution.
- Current batch pipeline is simpler and faster for CI — Kafka mode would be an
  opt-in flag (`--mode streaming`).

---

## Current State

Kafka is **not yet implemented**. The pipeline currently uses:

```
Generators → Parquet files → Bronze Spark jobs → Silver Delta → Gold Delta
```

This ADR records the intent and rationale so that the streaming migration has
documented context.

