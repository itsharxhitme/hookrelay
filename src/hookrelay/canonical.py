import json
from typing import Any
def canonical_json_bytes(value: object) -> bytes:
    
    try:
        json_object = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',',':'))
        
        encoded_object = json_object.encode('utf-8')
        
        return encoded_object
    
    except ValueError as err:
        raise ValueError("invalid JSON value") from err
    

def handle_duplicate_pairs(pairs: list[tuple[str,Any]]):
    
    dict_obj = {}
    
    for key, value in pairs:
        if key in dict_obj:
            raise ValueError("duplicate keys in JSON object")
        dict_obj[key] = value
        
    return dict_obj  

def parse_json_bytes(data: bytes) -> object:
        
        decoded = data.decode('utf-8')
        parsed = json.loads(decoded,object_pairs_hook=handle_duplicate_pairs)
        return parsed 