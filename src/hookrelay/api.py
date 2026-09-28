from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from hookrelay.services.validation import validate_event_request
app = FastAPI()


class ValidateEventRequest(BaseModel):
    event_type: str
    payload: dict[str,Any]


@app.get('/health')
def get_health():
    return {"status": "ok"}

@app.post('/validate-event')
def validate_event(body: ValidateEventRequest):
    return validate_event_request(body.event_type,body.payload)