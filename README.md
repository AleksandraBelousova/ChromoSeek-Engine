![alt text](https://img.shields.io/travis/com/your-username/ChromoSeek-Engine.svg?style=flat-square)

![alt text](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)

Elasticsearch-based system for the indexing and querying of genomic interval data formatted as BED or GFF/GTF files. System performance for spatial queries on genomic coordinates is achieved through Elasticsearch's native integer_range data type, which is indexed using BKD-trees within the underlying Lucene engine. Data ingestion is orchestrated via a Prefect pipeline that populates the index, while a FastAPI application provides a RESTful interface for executing interval intersection and aggregation queries against the dataset.
System Architecture
The system architecture is composed of three services, each containerised and orchestrated via Docker Compose, which defines a dependency graph where the API awaits a healthy Elasticsearch instance before starting.
Elasticsearch: A single-node Elasticsearch instance functions as the primary data store and query engine. A predefined index mapping specifies the integer_range type for the location field, enabling native interval query execution without requiring custom plugins or scripting.
FastAPI Application: The FastAPI application serves as the API gateway, responsible for translating inbound HTTP requests into the Elasticsearch Query DSL. It encapsulates all query logic and handles the serialization of responses.
Prefect Pipeline: A data ingestion pipeline, defined using Prefect, is executed as a command-line process within the API container's runtime environment. This pipeline handles file parsing, data transformation into JSON documents, and executes bulk indexing operations against the Elasticsearch Bulk API for maximal ingestion throughput.
System Deployment
Prerequisites
Docker Engine
Docker Compose
Procedure
Obtain the source code:
code
Bash
git clone https://github.com/your-username/ChromoSeek-Engine.git
cd ChromoSeek-Engine
Populate the data volume:
Place source data files (.bed, .gtf, .gff3) into the ./data/external/ directory, which is configured as a bind mount for the API container.
Instantiate services:
Instantiate and run the service containers in detached mode using the following command.
code
Bash
docker-compose up --build -d
Data Ingestion
To populate the Elasticsearch index, the Prefect pipeline must be executed. This command attaches to the running api container and initiates the Python module responsible for data ingestion.
code
Bash
docker-compose exec api python -m src.ingestion.pipelines
API Specification
The API is exposed on the host at http://localhost:8000. All endpoints expect and return application/json.
1. POST /find_overlaps
Performs an intersection query, retrieving all documents whose location field intersects with one or more of the provided genomic regions, with an optional filter on feature_type.
Request Body Schema:
code
JSON
{
  "regions": [
    {"chrom": "1", "start": 1000000, "end": 2000000}
  ],
  "feature_types": ["exon"]
}
curl Example:
code
Bash
curl -X POST "http://localhost:8000/find_overlaps" \
-H "Content-Type: application/json" \
-d '{"regions": [{"chrom": "1", "start": 1, "end": 50000000}], "feature_types": ["transcript"]}'
2. GET /features_by_gene/{gene_name}
Executes a two-stage query by first identifying the genomic coordinates of a specified gene symbol (by querying for its associated transcript feature) and subsequently executing an intersection query to find all features of a given feature_type_filter that overlap with those coordinates.
Query Parameters:
feature_type_filter (string, required): The target feature type for the second-stage intersection query.
curl Example:
code
Bash
curl -X GET "http://localhost:8000/features_by_gene/CYTB?feature_type_filter=GSM1598218"
3. GET /statistics/density
Executes a terms aggregation on the chrom field for all documents matching a specified feature_type, returning a count of features per chromosome.
Query Parameters:
feature_type (string, required): The feature type on which to perform the aggregation.
curl Example:
code
Bash
curl -X GET "http://localhost:8000/statistics/density?feature_type=GSM1598218"
Data Normalisation Prerequisite
The system performs exact keyword matching on the chrom field, meaning chromosome notations such as 1 and chr1 are treated as distinct values. Consequently, it is a mandatory pre-processing step to normalise all input data files to a consistent chromosome naming convention prior to ingestion to ensure the logical correctness of intersection queries.
Directory Layout
code
Code
chromoseek-engine/
├── data/external/
├── src/
│   ├── api/main.py
│   ├── elastic/
│   │   ├── client.py
│   │   └── mapping.json
│   └── ingestion/
│       ├── parsers.py
│       └── pipelines.py
├── .gitignore
├── docker-compose.yml
├── Dockerfile.api
├── requirements.txt
└── README.md
