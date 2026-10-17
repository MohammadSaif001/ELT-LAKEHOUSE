# Runbook — Kafka Recovery (Future / Streaming Mode)

| Field        | Value                               |
|--------------|-------------------------------------|
| **Severity** | P1 (streaming pipeline halted)       |
| **Owner**    | Mohammad Saif                       |
| **Updated**  | 2026-10-16                          |
| **Status**   | Draft — Kafka not yet implemented   |

---

> [!NOTE]
> Kafka streaming is a **planned feature** (see [ADR 002](../adr/002_why_kafka.md)).
> This runbook documents the intended recovery procedures for when the streaming
> mode is active. The current pipeline is batch-only (Parquet files → Spark).

---

## Overview

In streaming mode, data flows through:

```
Generators → Kafka Topics → Spark Structured Streaming → Bronze Delta → Silver Delta
```

One Kafka topic per entity:

| Topic | Producer | Consumer |
|-------|----------|----------|
| `elt.customers` | customer generator | Bronze customers job |
| `elt.products` | product generator | Bronze products job |
| `elt.sellers` | seller generator | Bronze sellers job |
| `elt.orders` | order generator | Bronze orders job |
| `elt.order_items` | order-item generator | Bronze order-items job |
| `elt.payments` | payment generator | Bronze payments job |
| `elt.reviews` | review generator | Bronze reviews job |

---

## Diagnosing Kafka Health

```bash
# Check if the broker is running (KRaft single-node)
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# List topics and verify they exist
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Check consumer group lag (Spark Structured Streaming uses auto-managed offsets)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group elt-spark-streaming \
    --describe
```

**Healthy output** — `LAG` column should be near 0 for a caught-up consumer:
```
TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
elt.orders     0          14823           14825           2
```

---

## Failure Scenarios

### Scenario 1 — Broker Not Reachable

**Symptom**:
```
ERROR | KafkaConsumer | Connection to broker localhost:9092 refused
org.apache.kafka.common.errors.TimeoutException: Topic elt.orders not found
```

**Fix**:
```bash
# Start the local KRaft broker
kafka-server-start.sh config/kraft/server.properties &

# Wait for the broker to be ready
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Restart the Spark streaming job
uv run python3 -m elt_pipeline --run-pipeline --mode streaming
```

---

### Scenario 2 — Topic Does Not Exist

**Symptom**:
```
ERROR | Structured Streaming | UnknownTopicOrPartitionException: elt.customers
```

**Fix**:
```bash
# Create all required topics (retention.ms = 7 days)
for topic in customers products sellers orders order_items payments reviews; do
  kafka-topics.sh --bootstrap-server localhost:9092 \
      --create --if-not-exists \
      --topic elt.$topic \
      --partitions 4 \
      --replication-factor 1 \
      --config retention.ms=604800000
done

# Verify
kafka-topics.sh --bootstrap-server localhost:9092 --list
```

---

### Scenario 3 — Streaming Job Crashed Mid-Run (Checkpoint Recovery)

Spark Structured Streaming checkpoints its progress in `checkpoints/<topic>/`.
On restart, it automatically resumes from the last committed offset.

**Fix**:
```bash
# Simply restart — Spark will resume from the checkpoint
uv run python3 -m elt_pipeline --run-pipeline --mode streaming
```

**If the checkpoint is corrupted**:
```bash
# WARNING: This will reprocess all messages from the beginning of the topic
rm -rf checkpoints/

uv run python3 -m elt_pipeline --run-pipeline --mode streaming
```

> [!CAUTION]
> Deleting checkpoints causes Spark to reprocess all retained messages.
> If Bronze Delta tables use `MERGE INTO` (idempotent), this is safe.
> If Bronze uses `append` mode, duplicate rows will be written.

---

### Scenario 4 — Consumer Group Lag Is Growing

**Symptom**: `LAG` in `kafka-consumer-groups.sh` is increasing every minute —
Spark cannot keep up with the producer rate.

**Diagnosis**:
```bash
# Check Spark UI at http://localhost:4040 → Structured Streaming tab
# Look at "Input Rate" vs "Processing Rate"
```

**Fix Options**:

| Option | Command / Config Change |
|--------|------------------------|
| Increase Spark parallelism | `shuffle_partitions: 8` in `spark_config.yaml` |
| Increase trigger interval | `.trigger(processingTime="30 seconds")` |
| Scale Kafka partitions | `kafka-topics.sh --alter --partitions 8` |
| Limit max records per batch | `.option("maxOffsetsPerTrigger", 10000)` |

---

### Scenario 5 — Message Deserialization Failure

**Symptom**:
```
ERROR | StructuredStreaming | SparkException: Failed to deserialize row
org.apache.spark.sql.catalyst.errors.package$TreeNodeException: execute, tree:...
```

**Cause**: A producer emitted a malformed message (wrong schema, null key, etc.)

**Fix**:
```bash
# Inspect the bad message
kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic elt.orders \
    --from-beginning \
    --max-messages 5

# If the topic contains corrupt data, reset the consumer offset to skip it:
kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --group elt-spark-streaming \
    --topic elt.orders \
    --reset-offsets \
    --to-latest \
    --execute
```

---

## Complete Kafka Reset (Development Only)

```bash
# Stop Spark streaming job first, then:
kafka-topics.sh --bootstrap-server localhost:9092 \
    --delete \
    --topic elt.customers,elt.products,elt.sellers,elt.orders,elt.order_items,elt.payments,elt.reviews

rm -rf checkpoints/

# Recreate topics and restart
```

> [!CAUTION]
> Deleting topics deletes all retained messages. All data must be re-generated
> by the producers. Never do this in production.

---

## Useful Commands Reference

```bash
# Produce a test message manually
echo '{"customer_id":"test-001","name":"Test User"}' | \
  kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic elt.customers

# Consume and pretty-print
kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic elt.customers \
    --from-beginning \
    --max-messages 3 | python3 -m json.tool

# Check broker config
kafka-configs.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --entity-type brokers \
    --entity-default
```

