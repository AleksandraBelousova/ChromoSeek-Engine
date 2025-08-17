import json
import glob
from pathlib import Path
from elasticsearch.helpers import bulk
from prefect import task, flow
from src.elastic.client import es_client
from src.ingestion.parsers import stream_file

INDEX_NAME = "genomic_features"
MAPPING_FILE = Path(__file__).parent.parent / "elastic/mapping.json"
DATA_DIR = Path(__file__).parent.parent.parent / "data/external"

@task
def create_index_if_not_exists():
    if not es_client.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' not found. Creating...")
        with open(MAPPING_FILE, 'r') as f:
            mapping = json.load(f)
        es_client.indices.create(index=INDEX_NAME, mappings=mapping)
        print(f"Index '{INDEX_NAME}' created successfully.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")

def _generate_bulk_actions(file_path: str, file_type: str, feature_type: str):
    for doc in stream_file(file_path, file_type, feature_type):
        yield {"_index": INDEX_NAME, "_source": doc}

@task(log_prints=True, retries=2, retry_delay_seconds=10)
def bulk_index_file(file_path: str, file_type: str, feature_type: str = "unknown"):
    print(f"Starting bulk indexing for {file_path}...")
    actions = _generate_bulk_actions(file_path, file_type, feature_type)
    success, failed = bulk(
        es_client,
        actions,
        chunk_size=10000,
        request_timeout=120,
        max_retries=3
    )
    
    print(f"Indexing complete for {file_path}. Success: {success}, Failed: {failed}")
    if failed:
        raise Exception(f"{failed} documents failed to index for file {file_path}.")

@flow(name="ChromoSeek Indexing Pipeline", log_prints=True)
def indexing_pipeline():
    create_index_if_not_exists()
    gtf_files = glob.glob(str(DATA_DIR / "*.gtf"))
    if gtf_files:
        bulk_index_file.submit(file_path=gtf_files[0], file_type='gtf')
    else:
        print("WARN: No GTF file found in data/external.")
    bed_files = glob.glob(str(DATA_DIR / "*.bed"))
    print(f"Found {len(bed_files)} BED files to index.")
    for bed_file in bed_files:
        feature_name = Path(bed_file).stem.split('_')[0]
        bulk_index_file.submit(
            file_path=bed_file,
            file_type="bed",
            feature_type=feature_name
        )
if __name__ == "__main__":
    indexing_pipeline()