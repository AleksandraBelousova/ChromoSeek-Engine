# ChromoSeek-Engine
Elasticsearch backend for genomic interval data (BED, GFF/GTF). Leverages the integer_range data type for performant spatial queries on genomic coordinates. Ingestion is managed by a Prefect pipeline, exposing a RESTful API via FastAPI for interval intersection and aggregation operations.
