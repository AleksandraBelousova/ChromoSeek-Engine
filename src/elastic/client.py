import os
from elasticsearch import Elasticsearch

def get_es_client() -> Elasticsearch:
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    client = Elasticsearch(
        hosts=[es_host],
        retry_on_timeout=True,
        max_retries=3
    )
    return client

# Singleton instance for the application
es_client = get_es_client()