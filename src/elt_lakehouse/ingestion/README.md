# Ingestion

This package moves source data into the Bronze layer and provides adapters for
other ingestion paths.

- `bronze/` contains one ingestion function per configured entity. These
  functions read generated Parquet and write Delta under `storage/bronze/`.
- `core/` contains shared readers, writers, and the generic ingestor.
- `bootstrap/` contains one-time loading helpers for source datasets.
- `kafka/` contains the planned Kafka producer, consumer, and topic helpers.
- `metadata/` contains ingestion metadata helpers.

Bronze ingestion is orchestrated by
`src/elt_lakehouse/spark/jobs/bronze_job.py`. Entity paths and enabled stages
are defined in [`metadata/entities.yaml`](../../../metadata/entities.yaml).
