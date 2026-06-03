# Modern E-Commerce Lakehouse

## Overview

**Modern E-Commerce Lakehouse** is an end-to-end data engineering solution that implements a modern data stack for e-commerce operations. This project showcases best practices in building scalable data pipelines using cloud-native technologies and open-source tools.

### Key Features

- **Real-time Data Ingestion**: Kafka-based streaming pipeline for continuous data ingestion
- **Medallion Architecture**: Bronze (raw) → Silver (cleaned) → Gold (analytics-ready) data layers
- **Apache Spark**: Distributed data processing and transformations
- **Apache Airflow**: Orchestration and workflow management
- **dbt**: Data transformation and modeling
- **Data Quality**: Comprehensive testing and validation frameworks
- **Monitoring & Observability**: Grafana dashboards and Prometheus metrics
- **Docker Containerization**: Complete environment as code with Docker Compose
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment

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
│   ├── faker_order_generator.py            # Generate order data
│   ├── payment_generator.py                # Generate payment data
│   └── customer_generator.py               # Generate customer data
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
│   └── gold/                               # Analytics data storage
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
- **Kafka**: Message broker for real-time event streaming
- **Generators**: Synthetic data generation for orders, payments, and customers
- **Consumers**: Stream processing and data ingestion

### Processing Layer
- **Apache Spark**: Distributed data processing engine
- **Transformations**: Silver layer cleaning and enrichment jobs
- **Schema Management**: Registry for data schema evolution

### Transformation & Modeling Layer
- **dbt**: SQL-based data transformation tool
- **Models**: Multi-layered data models (staging → silver → marts → gold)
- **Testing**: Data quality and integrity tests
- **Snapshots**: Historical tracking of dimension changes

### Storage Layer
- **Medallion Architecture**:
  - **Bronze**: Raw, immutable data source
  - **Silver**: Cleaned, deduplicated data
  - **Gold**: Analytics-ready, business-purpose data

### Orchestration
- **Apache Airflow**: DAG-based workflow orchestration
- **Task Dependencies**: Automated pipeline scheduling and monitoring

### Monitoring & Quality
- **Grafana**: Visualization and dashboarding
- **Prometheus**: Metrics collection and alerting
- **Data Quality Tests**: Validation rules for data integrity
- **Unit & Integration Tests**: Code quality assurance

### Infrastructure
- **Docker**: Containerized services (Spark, Airflow, Kafka, PostgreSQL)
- **Docker Compose**: Multi-container orchestration
- **CI/CD**: GitHub Actions for automated testing and deployment

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

4. **Run data generators**
   ```bash
   python generators/faker_order_generator.py
   python generators/payment_generator.py
   python generators/customer_generator.py
   ```

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

1. **Data Generation**: Create synthetic data using generators
2. **Ingestion**: Stream data via Kafka to Bronze layer
3. **Processing**: Transform data with Spark for Silver layer
4. **Modeling**: Build analytics models with dbt for Gold layer
5. **Monitoring**: Track pipeline health via Grafana dashboards
6. **Testing**: Validate data quality with dbt tests and custom validators

---

## Key Features

✅ Real-time streaming architecture  
✅ Scalable distributed processing  
✅ Modern data stack (Spark + Airflow + dbt)  
✅ Comprehensive data quality checks  
✅ Production-ready monitoring  
✅ Fully containerized with Docker  
✅ CI/CD pipeline with GitHub Actions  
✅ Documented with ADR patterns  

---

## Contributing

Contributions are welcome! Please follow the development guidelines in [docs/decisions.md](docs/decisions.md).

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the development team.