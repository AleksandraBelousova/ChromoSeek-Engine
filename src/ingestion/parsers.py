import re
from pathlib import Path
from typing import Iterator, Dict, Any, Generator

def _parse_gtf_attributes(attr_string: str) -> Dict[str, str]:
    return dict(re.findall(r'(\S+)\s+"([^"]+)";', attr_string))
def _gtf_record_to_doc(record: list[str], source_file: str) -> Dict[str, Any] | None:
    feature_type = record[2]
    if feature_type not in ('transcript', 'exon', 'CDS'):
        return None
    attributes = _parse_gtf_attributes(record[8])
    gene_name = attributes.get("gene_name")
    if not gene_name:
        return None
    searchable_feature_type = 'gene' if feature_type == 'transcript' else feature_type
    feature_id = attributes.get("transcript_id", gene_name)
    return {
        "chrom": record[0],
        "location": {"gte": int(record[3]), "lt": int(record[4]) + 1},
        "strand": record[6],
        "score": float(record[5]) if record[5] != '.' else 0.0,
        "feature_type": searchable_feature_type, 
        "feature_id": feature_id,
        "gene_name": gene_name,
        "source_file": source_file,
    }
def _bed_record_to_doc(record: list[str], source_file: str, feature_type: str) -> Dict[str, Any]:
    return {
        "chrom": record[0],
        "location": {"gte": int(record[1]), "lt": int(record[2])},
        "feature_id": record[3] if len(record) > 3 else f"{record[0]}:{record[1]}-{record[2]}",
        "score": float(record[4]) if len(record) > 4 and record[4] != '.' else 0.0,
        "strand": record[5] if len(record) > 5 else '.',
        "feature_type": feature_type,
        "source_file": source_file,
    }

def stream_file(file_path: str, file_type: str, feature_type_override: str = "unknown") -> Generator[Dict[str, Any], None, None]:
    source_filename = Path(file_path).name
    parser_func = _gtf_record_to_doc if file_type == 'gtf' else _bed_record_to_doc
    
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith(('#', 'track', 'browser')):
                continue
            
            fields = line.strip().split('\t')
            try:
                if file_type == 'gtf':
                    doc = _gtf_record_to_doc(fields, source_filename)
                    if doc:
                        yield doc
                else: # bed
                    yield _bed_record_to_doc(fields, source_filename, feature_type_override)
            except (ValueError, IndexError) as e:
                print(f"WARN: Skipping malformed line in {source_filename}: {line.strip()} | Error: {e}")