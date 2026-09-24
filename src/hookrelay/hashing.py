from hashlib import sha256
from hookrelay.canonical import canonical_json_bytes

def sha256_hex(data: bytes) -> str:

    return sha256(data).hexdigest()

def hash_json_obj(obj: object) -> str:
    
    decoded_obj = canonical_json_bytes(obj)
    
    return sha256_hex(decoded_obj)
