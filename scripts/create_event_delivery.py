from sqlalchemy import select
from hookrelay.db.session import session_scope
from hookrelay.db.models import Event, Delivery
from hookrelay.hashing import sha256_hex
import uuid
import asyncio
async def create_event_delivery():
    
    async with session_scope() as session:
        
        event_id = uuid.uuid4().hex
        payload = b'{"user_id":"12"}'
        payload_hash = sha256_hex(payload)
        new_event = Event(id=event_id, tenant_id = 'local-tenant', event_type="user.created", payload= payload, payload_hash = payload_hash)
        session.add(new_event)
        await session.flush()
        
        delivery_id = uuid.uuid4().hex
        new_delivery = Delivery(id = delivery_id, event_id = event_id, endpoint_id='local-endpoint')
        session.add(new_delivery)
        
def main():
    asyncio.run(create_event_delivery())
    
if __name__ == "__main__":
    main()