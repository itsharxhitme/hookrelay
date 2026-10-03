from fastapi import FastAPI,status
from pydantic import BaseModel
from typing import Any
from hookrelay.db.session import session_scope
from hookrelay.services.ingest import ingest_event
app = FastAPI()

TENANT_ID = "local-tenant" # TODO(D23): replace with authenticated tenant
class CreateEventRequest(BaseModel):
    event_type: str
    payload: dict[str,Any]


@app.get('/health')
def get_health():
    return {"status": "ok"}

@app.post('/events',status_code=status.HTTP_202_ACCEPTED)
async def create_event(body: CreateEventRequest):
    
    async with session_scope() as session:
        
        result = await ingest_event(session = session, tenant_id = TENANT_ID, event_type = body.event_type, payload = body.payload)
        
    return result