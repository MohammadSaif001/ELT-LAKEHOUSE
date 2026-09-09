"""
Freshness Checks Module

This module provides data quality checks to ensure that data in the lakehouse meets
freshness requirements. Freshness validation verifies that data is recent and not stale
by checking timestamps and ensuring data was ingested/updated within acceptable time windows.

Key Responsibilities:
- Validate that records have recent timestamps (not older than configured thresholds)
- Identify stale data that exceeds maximum age tolerances
- Quarantine records that fail freshness validation
- Log freshness validation metrics and issues

The module works in conjunction with data quality contracts that define acceptable
freshness criteria for each dataset. Records failing freshness checks are separated
into a quarantine dataset for further investigation or remediation.
"""
