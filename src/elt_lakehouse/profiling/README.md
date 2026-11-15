# Dataset profiling

The profiling modules inspect the downloaded Olist source data and write
summary JSON artifacts used to configure and understand synthetic data
generation.

`common.py` provides shared file loading and profile persistence. The entity
modules generate profiles for customers, locations, sellers, products, orders,
order items, payments, and reviews.

Profiling is run by the setup action:

```bash
uv run elt --setup
```

Profiles are local generated artifacts. If source data or profile schemas
change, regenerate them before building pools and datasets.
