from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from hookrelay.db.models import DeliveryAttempt
@dataclass(frozen=True)
class ClaimedWork:
    event_id: str
    endpoint_id: str
    delivery_id: str
    payload: bytes
    attempt_id: str
    attempt_number: int 
    lease_token: str
    lease_expiry: datetime
        
async def claim_one_delivery(session: AsyncSession) -> ClaimedWork | None:
    
    available_delivery = (await session.execute(text(
        '''
        SELECT d.id as delivery_id, d.event_id, d.endpoint_id, e.payload
        FROM deliveries d
        JOIN events e on e.id = d.event_id
        WHERE d.status = 'pending' AND d.due_time <= now()
        ORDER BY d.due_time
        LIMIT 1
        FOR UPDATE OF d SKIP LOCKED
        '''
    ))).fetchone()
    if available_delivery is None:
        return None
    
    lease_token = uuid.uuid4().hex
    updated_delivery = (await session.execute(text('''
        UPDATE deliveries 
        SET status = 'in_progress', lease_token = :lease_token , lease_expiry = now() + interval '60 seconds', attempt_count = attempt_count + 1
        WHERE id = :id
        RETURNING attempt_count, lease_expiry
        
        '''),{"lease_token": lease_token, "id": available_delivery.delivery_id})).fetchone()
    
    attempt_id = uuid.uuid4().hex
    session.add(DeliveryAttempt(
        id = attempt_id,
        delivery_id = available_delivery.delivery_id,
        attempt_number = updated_delivery.attempt_count,
    ))
    
    return ClaimedWork(
        event_id=available_delivery.event_id,
        endpoint_id=available_delivery.endpoint_id,
        delivery_id= available_delivery.delivery_id,
        payload= available_delivery.payload,
        lease_token=lease_token,
        lease_expiry=updated_delivery.lease_expiry,
        attempt_id=attempt_id,
        attempt_number=updated_delivery.attempt_count
    )
    
    