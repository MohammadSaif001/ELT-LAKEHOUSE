# Synthetic data generators

The generators create the local Olist-style dataset consumed by the ELT
pipeline. Pool builders create reusable customer, product, and seller IDs;
dataset builders then generate related records and write Parquet files under
`storage/generated/`.

`base/` contains shared chunking, multiprocessing, distribution, loading, and
saving helpers. Entity folders contain the domain-specific generators and build
functions.

Generation is controlled by [`config/generator_config.yaml`](../../../config/generator_config.yaml).
Use `--build-pool` before `--build-dataset`, or run `--run-pipeline` to execute
the dependency order automatically. Generated files are local artifacts and
should not be committed.
