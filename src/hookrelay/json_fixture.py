import json
from pathlib import Path
def load_fixture(file_path: str | Path, required_key: str) -> dict[str,any]:
    
    with open(file_path , mode='r', encoding='utf-8') as f:
        decoded = json.load(f)
        if not isinstance(decoded,dict):
            raise TypeError(f"Expected JSON object (dict), got {type(decoded).__name__} | file path : {file_path}")
        if required_key not in decoded:
            raise ValueError(f"Missing Required Field : {required_key} | file path : {file_path}")
        return decoded
    