"""Pipeline Monitoring Dashboard.

A read-only Flask application that surfaces the operational status of the
ELT lakehouse pipeline (pool generation -> dataset generation -> bronze
ingestion) by reading the project's existing metadata files, application
log, and storage layers. It does not generate or fabricate any pipeline
data; it only reports what the pipeline itself has already written.
"""
