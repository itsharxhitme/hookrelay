import time
import hmac
import hashlib

VERSION = "v1"
CLOCK_TOLERANCE_SECONDS = 300
def current_timestamp() -> int:
    return int(time.time())


def _build_message(timestamp: int, delivery_id: str, payload: bytes) -> bytes:
    prefix = f"{VERSION}:{timestamp}:{delivery_id}:"
    return prefix.encode("utf-8") + payload

def sign_payload(secret: str, delivery_id: str, timestamp: int ,payload: bytes) -> str:
    
    message = _build_message(timestamp,delivery_id,payload)
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return signature

def build_signature_header(secret: str, delivery_id: str, timestamp: int ,payload: bytes) -> str:
    
    digest = sign_payload(secret,delivery_id,timestamp,payload)
    
    return f"{VERSION}:{timestamp}:{delivery_id}:{digest}"

def verify_signature(secret: str, header: str, payload) -> bool:
    
    parts = header.split(':')
    if len(parts) != 4:
        return False
    version, ts_str, delivery_id, provided_digest = parts
    
    if version != VERSION: 
        return False
    
    try: 
        timestamp = int(ts_str)
    except ValueError: 
        return False
    
    if abs(current_timestamp() - timestamp) > CLOCK_TOLERANCE_SECONDS: 
        return False
    
    expected = sign_payload(secret, delivery_id, timestamp, payload)
    
    return hmac.compare_digest(provided_digest, expected)
    
    