from hookrelay.db.models import Endpoint, Delivery, Event
from typing import Any
from hookrelay.canonical import canonical_json_bytes
from hookrelay.hashing import sha256_hex
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


async def find_enabled_endpoint_ids(session: AsyncSession, tenant_id: str):
    
        stmt = select(Endpoint.id).where(Endpoint.tenant_id == tenant_id,Endpoint.enabled.is_(True))
        
        result = await session.execute(stmt)
        

        return list(result.scalars().all())


async def ingest_event(session: AsyncSession, tenant_id: str, event_type: str, payload: dict[str,Any]):
   
 
    payload_bytes = canonical_json_bytes(payload)
    payload_hash = sha256_hex(payload_bytes)
    event_id = uuid.uuid4().hex
            
    session.add(Event(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        payload=payload_bytes,
        payload_hash=payload_hash
    ))
    await session.flush() 
    endpoint_ids = await find_enabled_endpoint_ids(session, tenant_id=tenant_id)
    
    for endpoint_id in endpoint_ids:
            
        session.add(Delivery(
            id=uuid.uuid4().hex,
            event_id=event_id,
            endpoint_id=endpoint_id
        ))
        
    return {"event_id":event_id, "delivery_count":len(endpoint_ids)}