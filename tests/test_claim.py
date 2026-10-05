import pytest
import uuid
import asyncio
from sqlalchemy import text, delete
from hookrelay.db.session import session_scope
from hookrelay.db.models import Event, Delivery, Endpoint
from hookrelay.worker.claim import claim_one_delivery
from hookrelay.hashing import sha256_hex

@pytest.fixture
async def seeded_delivery():
    async with session_scope() as session:
        await session.execute(text('DELETE from delivery_attempts'))
        await session.execute(text('DELETE from deliveries'))
        await session.execute(text('DELETE from events'))
        
        event_id = uuid.uuid4().hex
        delivery_id = uuid.uuid4().hex
        payload = b'{"user_id":"user_id1"}'
        payload_hash = sha256_hex(payload)
        
        session.add(Event(id=event_id, tenant_id='local-tenant',event_type='user.created', payload=payload, payload_hash=payload_hash))
        await session.flush()
        session.add(Delivery(id=delivery_id,event_id=event_id,endpoint_id='local-endpoint'))

    yield {"event_id": event_id, "delivery_id": delivery_id}
    
    async with session_scope() as session:
        await session.execute(text('DELETE from delivery_attempts'))
        await session.execute(text('DELETE from deliveries'))
        await session.execute(text('DELETE from events'))


async def test_only_one_concurrent_claim_wins(seeded_delivery):
    
    async def do_claim():
        async with session_scope() as session:
            return await claim_one_delivery(session)
       
    
    result = await asyncio.gather(do_claim(), do_claim())
    
    winners = [r for r in result if r is not None]
    losers = [r for r in result if r is None]
    
    assert len(winners) == 1
    assert len(losers) == 1

async def test_claim_does_not_block_unrelated_rows(seeded_delivery):
    
    delivery_id = uuid.uuid4().hex
    
    async with session_scope() as session:
        
        endpoint_id = uuid.uuid4().hex
        session.add(Endpoint(id=endpoint_id,tenant_id = 'local-tenant',url='http://127.0.0.1:8002/receive',signing_secret_ref='FAKE_SECRET_REF'))
        await session.flush()
        session.add(Delivery(id=delivery_id,event_id=seeded_delivery['event_id'],endpoint_id=endpoint_id))
        
    
    try:
        
        claim_started = asyncio.Event()
        release_claim = asyncio.Event()
            
        async def slow_claim():
            async with session_scope() as session:
                claimed = await claim_one_delivery(session)
                claim_started.set()
                await release_claim.wait()
                return claimed
            
        async def update_others():
            await claim_started.wait()
            async with session_scope() as session:
                await session.execute(text(
                '''
                    UPDATE deliveries 
                    SET due_time = now() 
                    WHERE id = :delivery_id          
                '''
                ),{"delivery_id":delivery_id})
                    
            return "updated"
                
        claim_task = asyncio.create_task(slow_claim())
        update_task = asyncio.create_task(update_others())
                
        result = await asyncio.wait_for(update_task, timeout=2.0)
        assert result == "updated"
        
        release_claim.set()
        claimed = await claim_task
        assert claimed is not None
        assert claimed.delivery_id != delivery_id
    finally:
        
        async with session_scope() as session:
            await session.execute(delete(Delivery).where(Delivery.id == delivery_id))
            await session.execute(delete(Endpoint).where(Endpoint.id == endpoint_id))