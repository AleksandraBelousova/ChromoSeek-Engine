from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from src.elastic.client import es_client

INDEX_NAME = "genomic_features"
MAX_PAGE_SIZE = 5000

app = FastAPI(
    title="ChromoSeek Engine",
    description="A high-performance API for querying genomic interval data.",
    version="1.0.0-stable"
)

class GenomicRegion(BaseModel):
    chrom: str = Field(..., description="Chromosome name, e.g., '1' or 'chr1'")
    start: int = Field(..., ge=0, description="Start coordinate")
    end: int = Field(..., ge=0, description="End coordinate")

class OverlapRequest(BaseModel):
    regions: List[GenomicRegion]
    feature_types: List[str] = Field(default=[], description="Optional list of feature types to filter")

@app.post("/find_overlaps", summary="Find features overlapping with given regions")
def find_overlaps(
    request: OverlapRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=MAX_PAGE_SIZE)
) -> List[Dict[str, Any]]:
    if not request.regions:
        return []
    region_queries = [
        {"bool": {"filter": [
            {"term": {"chrom": region.chrom}},
            {"range": {"location": {"gte": region.start, "lte": region.end, "relation": "intersects"}}}
        ]}} for region in request.regions
    ]
    query = {"bool": {"should": region_queries, "minimum_should_match": 1}}
    if request.feature_types:
        query["bool"].setdefault("filter", []).append({"terms": {"feature_type": request.feature_types}})
    try:
        response = es_client.search(index=INDEX_NAME, query=query, from_=skip, size=limit)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch query failed: {e}")

@app.get("/features_by_gene/{gene_name}", summary="Get features overlapping a specific gene")
def get_features_by_gene(gene_name: str, feature_type_filter: str) -> List[Dict[str, Any]]:
    gene_query = {"bool": {"filter": [
        {"term": {"feature_type": "transcript"}},
        {"term": {"gene_name": gene_name}}
    ]}}
    try:
        response = es_client.search(index=INDEX_NAME, query=gene_query, size=1)
        if not response["hits"]["hits"]:
            raise HTTPException(status_code=404, detail=f"Gene '{gene_name}' (transcript) not found.")
        
        gene_doc = response["hits"]["hits"][0]["_source"]
        overlap_request = OverlapRequest(
            regions=[GenomicRegion.model_validate({"chrom": gene_doc["chrom"], "start": gene_doc["location"]["gte"], "end": gene_doc["location"]["lt"]})],
            feature_types=[feature_type_filter]
        )
        return find_overlaps(request=overlap_request, skip=0, limit=MAX_PAGE_SIZE)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.get("/statistics/density", summary="Get feature density per chromosome")
def get_density_statistics(feature_type: str) -> Dict[str, int]:
    query = {"bool": {"filter": {"term": {"feature_type": feature_type}}}}
    aggs = {"features_per_chrom": {"terms": {"field": "chrom", "size": 100}}}
    
    try:
        response = es_client.search(index=INDEX_NAME, query=query, aggs=aggs, size=0, track_total_hits=False)
        buckets = response["aggregations"]["features_per_chrom"]["buckets"]
        return {bucket["key"]: bucket["doc_count"] for bucket in buckets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch aggregation failed: {e}")