# Modern E-Commerce Lakehouse

## Overview

**Modern E-Commerce Lakehouse** is an end-to-end data engineering solution that implements a modern data stack for e-commerce operations. This project showcases best practices in building scalable data pipelines using cloud-native technologies and open-source tools.

### Key Features

- **Real-time Data Ingestion**: Kafka-based streaming pipeline for continuous data ingestion.
- **Medallion Architecture**: Bronze (raw) → Silver (cleaned) → Gold (analytics-ready) data layers.
- **Apache Spark**: Distributed data processing and transformations.
- **Apache Airflow**: Orchestration and workflow management.
- **dbt**: Data transformation and modeling.
- **Data Quality & Referential Integrity**: Automated test validation rules executing key checks across all generated datasets.
- **Monitoring & Observability**: Grafana dashboards and Prometheus metrics.
- **Docker Containerization**: Complete environment as code with Docker Compose.
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment.

---

## Project Structure

```
modern-ecommerce-lakehouse/
│
├── airflow/
│   ├── dags/
│   │   └── ecommerce_pipeline.py          # Main orchestration DAG
│   │
│   └── requirements.txt                    # Airflow dependencies
│
├── docker/
│   ├── docker-compose.yml                  # Docker Compose configuration
│   ├── spark/                              # Spark service configuration
│   ├── airflow/                            # Airflow service configuration
│   ├── kafka/                              # Kafka service configuration
│   └── postgres/                           # PostgreSQL service configuration
│
├── generators/
│   ├── base/                               # Reusable helpers & pool managers
│   │   ├── data_loading.py                 # Load generated datasets
│   │   ├── data_saving.py                  # Save generated datasets
│   │   ├── pool_builder.py                 # Utility to build entities from scratch
│   │   └── pool_manger.py                  # Handles loading and saving metadata pools
│   │
│   ├── customers/                          # Customer & geolocation generation
│   │   ├── build_customers.py              # Customer dataset builder
│   │   ├── build_geolocations.py           # Geolocation dataset builder
│   │   ├── customer_generator.py           # Generate individual customer records
│   │   └── customer_location_generator.py  # Generate coordinates matched to customers
│   │
│   ├── orders/                             # Order & order item generation
│   │   ├── build_orders.py                 # Builds orders & order items datasets
│   │   ├── order_generator.py              # Generates orders using customer pool
│   │   └── order_item_generator.py         # Generates order items using product/seller pools
│   │
│   ├── payments/                           # Payment generation
│   │   ├── build_payments.py               # Payments dataset builder
│   │   └── payment_generator.py            # Generates payment events based on order values
│   │
│   ├── products/                           # Product pool generation
│   │   ├── build_products.py               # Products dataset builder
│   │   └── product_generator.py            # Generates product entries using seller pool
│   │
│   ├── reviews/                            # Review generation
│   │   ├── build_reviews.py                # Reviews dataset builder
│   │   └── review_generator.py             # Generates satisfaction reviews for delivered orders
│   │
│   ├── sellers/                            # Seller generation
│   │   ├── build_sellers.py                # Sellers dataset builder
│   │   └── seller_generator.py             # Generates seller demographics
│   │
│   └── build_dataset.py                    # Orchestrates all generators in dependency order
│
├── ingestion/
│   ├── kafka_producer.py                   # Kafka data producer
│   ├── kafka_consumer.py                   # Kafka data consumer
│   └── stream_to_bronze.py                 # Stream ingestion to Bronze layer
│
├── spark/
│   ├── silver/
│   │   ├── orders_silver.py                # Orders transformation job
│   │   ├── payments_silver.py              # Payments transformation job
│   │   └── customers_silver.py             # Customers transformation job
│   │
│   └── utils/
│       ├── schema_registry.py              # Schema management
│       ├── spark_session.py                # Spark session initialization
│       └── validations.py                  # Data validation utilities
│
├── dbt/
│   ├── models/
│   │   ├── staging/                        # Staging models
│   │   ├── silver/                         # Silver layer models
│   │   ├── marts/                          # Business-facing marts
│   │   └── gold/                           # Gold layer analytics models
│   │
│   ├── tests/                              # dbt test cases
│   ├── macros/                             # dbt macros and utilities
│   ├── snapshots/                          # Type-2 dimension snapshots
│   └── dbt_project.yml                     # dbt configuration
│
├── storage/
│   ├── bronze/                             # Raw data storage
│   ├── silver/                             # Cleaned data storage
│   ├── gold/                               # Analytics data storage
│   └── generated/                          # Structurally equivalent generated datasets
│
├── monitoring/
│   ├── grafana/                            # Grafana dashboard configuration
│   ├── prometheus/                         # Prometheus metrics configuration
│   └── logs/                               # Application logs
│
├── tests/
│   ├── unit/                               # Unit tests
│   ├── integration/                        # Integration tests
│   └── quality/                            # Data quality tests
│
├── notebooks/
│   └── exploration.ipynb                   # Jupyter notebooks for exploration
│
├── docs/
│   ├── architecture.png                    # Architecture diagram
│   ├── lineage.png                         # Data lineage diagram
│   └── decisions.md                        # ADR - Architectural Decision Records
│
├── .github/
│   └── workflows/
│       └── ci.yml                          # GitHub Actions CI/CD pipeline
│
├── README.md                               # This file
└── requirements.txt                        # Python dependencies
```

---

## Component Overview

### Data Ingestion Layer
- **Kafka**: Message broker for real-time event streaming.
- **Generators**: Synthetic data generation mapping to Olist database structures.
- **Consumers**: Stream processing and data ingestion.

### Processing Layer
- **Apache Spark**: Distributed data processing engine.
- **Transformations**: Silver layer cleaning and enrichment jobs.
- **Schema Management**: Registry for data schema evolution.

### Transformation & Modeling Layer
- **dbt**: SQL-based data transformation tool.
- **Models**: Multi-layered data models (staging → silver → marts → gold).
- **Testing**: Data quality and integrity tests.
- **Snapshots**: Historical tracking of dimension changes.

### Storage Layer
- **Medallion Architecture**:
  - **Bronze**: Raw, immutable data source.
  - **Silver**: Cleaned, deduplicated data.
  - **Gold**: Analytics-ready, business-purpose data.
  - **Generated**: Structurally equivalent target dataset mimicking the Olist schema.

### Orchestration
- **Apache Airflow**: DAG-based workflow orchestration.
- **Task Dependencies**: Automated pipeline scheduling and monitoring.

### Monitoring & Quality
- **Grafana**: Visualization and dashboarding.
- **Prometheus**: Metrics collection and alerting.
- **Data Quality Tests**: Validation rules for data integrity.
- **Unit & Integration Tests**: Code quality assurance.

### Infrastructure
- **Docker**: Containerized services (Spark, Airflow, Kafka, PostgreSQL).
- **Docker Compose**: Multi-container orchestration.
- **CI/CD**: GitHub Actions for automated testing and deployment.

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd modern-ecommerce-lakehouse
   ```

2. **Start services with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

3. **Access Services**
   - Airflow UI: http://localhost:8080
   - Spark: http://localhost:7077
   - Grafana: http://localhost:3000
   - Kafka: localhost:9092

4. **Run target dataset generation and referential checks**
   ```bash
   python3 -m generators.build_dataset
   ```

---

## Dataset Information

**Olist source files are excluded from version control due to repository size.** The raw datasets are stored in `data/raw/olist/` and are not committed to Git as they are large files.

**Profiling metadata and distributions** are used as a source for generators and are stored under `data/profiling/` and `generators/base/`.
The generator pipeline loads pre-computed pools from `metadata/pools/` (e.g. `customer_pool.json`, `product_pool.json`) to create a unified set of target datasets in `storage/generated/`:
1. `generated_customers_data.json`
2. `generated_geolocation_data.json`
3. `generated_sellers_data.json`
4. `generated_products_data.json`
5. `generated_orders_data.json`
6. `generated_order_items_data.json`
7. `generated_payments_data.json`
8. `generated_reviews_data.json`

Foreign-key integrity is validated automatically at the end of the generation run.

---

## Technology Stack

| Component | Purpose |
|-----------|---------|
| Apache Spark | Distributed data processing |
| Apache Airflow | Workflow orchestration |
| dbt | SQL data transformation |
| Kafka | Event streaming |
| PostgreSQL | Metadata & configuration storage |
| Grafana | Monitoring & visualization |
| Prometheus | Metrics collection |
| Docker | Containerization |
| Python | Scripting & data generation |

---

## Development Workflow

1. **Data Generation**: Create synthetic Olist-compliant data using `python3 -m generators.build_dataset`.
2. **Ingestion**: Stream data via Kafka to Bronze layer.
3. **Processing**: Transform data with Spark for Silver layer.
4. **Modeling**: Build analytics models with dbt for Gold layer.
5. **Monitoring**: Track pipeline health via Grafana dashboards.
6. **Testing**: Validate data quality with dbt tests and custom validators.

---

## Contributing

Contributions are welcome! Please follow the development guidelines in [docs/decisions.md](docs/decisions.md).

---

## License

This project is licensed under the MIT License - see LICENSE file for details.