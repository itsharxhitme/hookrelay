from typing import Any

def validate_event_request(event_type: str, payload: dict[str,Any]):
    return {"valid": True, "event_type": event_type , "stored": False}