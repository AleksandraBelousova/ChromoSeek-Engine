# Intersectome

A high-performance search engine for genomic interval data, optimised for rapid overlap and aggregation queries.

The system indexes standard bioinformatics formats (BED, GTF/GFF) and provides a low-latency API. Performance for spatial queries is achieved through Elasticsearch's native `integer_range` data type, which is indexed using BKD-trees within the underlying Lucene engine.

---

### 🏗️ System Architecture

The architecture is composed of three containerised services orchestrated via Docker Compose. The dependency graph ensures the API awaits a healthy Elasticsearch instance before starting.

*   **Elasticsearch:** A single-node instance acts as the primary data store and query engine. A predefined index mapping enables native interval query execution without requiring custom plugins.

*   **FastAPI Application:** Serves as the API gateway, responsible for translating inbound HTTP requests into the Elasticsearch Query DSL and handling the serialisation of responses.

*   **Prefect Pipeline:** A data ingestion pipeline handles file parsing, data transformation into JSON documents, and executes bulk indexing operations against the Elasticsearch Bulk API for maximal ingestion throughput.

---

### 🚀 Getting Started

**Prerequisites:**
*   Docker Engine
*   Docker Compose

**Procedure:**

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/AleksandraBelousova/Queryome.git
    cd Queryome
    ```

2.  **Populate the Data Directory**
    Place your source data files (`.bed`, `.gtf`, `.gff`) into the `./data/external/` directory.

3.  **Launch Services**
    Instantiate and run the service containers in detached mode.
    ```bash
    docker-compose up --build -d
    ```

4.  **Run Data Ingestion**
    Execute the Prefect pipeline to populate the Elasticsearch index.
    ```bash
    docker-compose exec api python -m src.ingestion.pipelines
    ```

---

### API Specification

The API is exposed on the host at `http://localhost:8000`. All endpoints expect and return `application/json`.

#### `POST /find_overlaps`
> Performs an intersection query, retrieving all documents whose `location` field intersects with one or more provided genomic regions.

*   **Request Body Schema:**
    ```json
    {
      "regions": [
        {"chrom": "1", "start": 1000000, "end": 2000000}
      ],
      "feature_types": ["exon"]
    }
    ```

#### `GET /features_by_gene/{gene_name}`
> Executes a two-stage query: first identifying the genomic coordinates of a specified gene symbol, then finding all features of a given type that overlap with those coordinates.

*   **Query Parameters:** `feature_type_filter` (string, required)
*   **`curl` Example:**
    ```bash
    curl "http://localhost:8000/features_by_gene/CYTB?feature_type_filter=GSM1598218"
    ```

#### `GET /statistics/density`
> Executes a `terms` aggregation on the `chrom` field for a specified `feature_type`, returning a count of features per chromosome.

*   **Query Parameters:** `feature_type` (string, required)
*   **`curl` Example:**
    ```bash
    curl "http://localhost:8000/statistics/density?feature_type=GSM1598218"
    ```
---

### ️🛡️ Security Advisory & Production Use

> This is a pet project. In its current configuration, the system is secure only for local development in a trusted network. It is **not** intended for deployment in a production environment without significant modifications.

The following action plan is required for migration to a production environment:
1.  Enable X-Pack Security in Elasticsearch and configure TLS encryption.
2.  Create a dedicated, low-privilege Elasticsearch user for the API and use its credentials via environment variables.
3.  Implement pagination and request size limits in the API to protect against denial-of-service attacks.
4.  Modify the `Dockerfile` to run the API service from a non-root user.
5.  Integrate vulnerability scanners for dependencies and Docker images into the build process.

### ⚠️ Data Normalisation Prerequisite

The system performs exact keyword matching on the `chrom` field. This means chromosome notations such as `1` and `chr1` are treated as distinct values. Normalising all input data to a consistent chromosome naming convention prior to ingestion is a mandatory pre-processing step to ensure the logical correctness of queries.

### 📁 Directory Layout
