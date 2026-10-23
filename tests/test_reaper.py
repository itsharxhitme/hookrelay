import pytest
from hookrelay.db.session import session_scope
from sqlalchemy import text
import uuid
from hookrelay.hashing import sha256_hex
from hookrelay.db.models import Event, Delivery, DeliveryAttempt, Endpoint
from datetime import datetime, timezone, timedelta
from hookrelay.domain import ClaimedWork
from hookrelay.worker.reaper import reap_expired_leases
from hookrelay.bootstrap import SECRET_REF, TENANT_ID
@pytest.fixture
async def expired_claimed_delivery():
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))
        
        event_id = uuid.uuid4().hex
        payload = b'{"user_id":"12"}'
        payload_hash = sha256_hex(payload)
        new_event = Event(id=event_id, tenant_id = 'local-tenant', event_type="user.created", payload= payload, payload_hash = payload_hash)
        session.add(new_event)
        await session.flush()
        
        delivery_id = uuid.uuid4().hex
        lease_token = uuid.uuid4().hex
        lease_expiry = datetime.now(timezone.utc) - timedelta(seconds=60)
        new_delivery = Delivery(id = delivery_id, event_id = event_id, endpoint_id='local-endpoint', status = 'in_progress', lease_token= lease_token, lease_expiry = lease_expiry, attempt_count = 1)
        
        session.add(new_delivery)
        await session.flush()
        
        attempt_id = uuid.uuid4().hex
        new_attempt = DeliveryAttempt(id = attempt_id, delivery_id = delivery_id, attempt_number = 1)
        session.add(new_attempt)
    
    claimed = ClaimedWork(
        event_id=event_id,
        endpoint_id='local-endpoint',
        delivery_id=delivery_id,
        payload=payload,
        attempt_id=attempt_id,
        attempt_number=1,
        lease_token=lease_token,
        lease_expiry=lease_expiry
    )
    yield claimed
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))    
        
@pytest.fixture
async def live_claimed_delivery():
    
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))
        
        event_id = uuid.uuid4().hex
        payload = b'{"user_id":"12"}'
        payload_hash = sha256_hex(payload)
        new_event = Event(id=event_id, tenant_id = 'local-tenant', event_type="user.created", payload= payload, payload_hash = payload_hash)
        session.add(new_event)
        await session.flush()
        
        delivery_id = uuid.uuid4().hex
        lease_token = uuid.uuid4().hex
        lease_expiry = datetime.now(timezone.utc) + timedelta(seconds=60)
        new_delivery = Delivery(id = delivery_id, event_id = event_id, endpoint_id='local-endpoint', status = 'in_progress', lease_token= lease_token, lease_expiry = lease_expiry, attempt_count = 1)
        
        session.add(new_delivery)
        await session.flush()
        
        attempt_id = uuid.uuid4().hex
        new_attempt = DeliveryAttempt(id = attempt_id, delivery_id = delivery_id, attempt_number = 1)
        session.add(new_attempt)
    
    claimed = ClaimedWork(
        event_id=event_id,
        endpoint_id='local-endpoint',
        delivery_id=delivery_id,
        payload=payload,
        attempt_id=attempt_id,
        attempt_number=1,
        lease_token=lease_token,
        lease_expiry=lease_expiry
    )
    yield claimed
    async with session_scope() as session:
        await session.execute(text("DELETE FROM delivery_attempts"))
        await session.execute(text("DELETE FROM deliveries"))
        await session.execute(text("DELETE FROM events"))    
        

async def test_reaps_expired_leases(expired_claimed_delivery):
    
    claimed = expired_claimed_delivery
    
    async with session_scope() as session:
        
        reaped = await reap_expired_leases(session=session, batch_size=10)
        
    assert reaped == 1
    
    async with session_scope() as session:
        delivery = await session.get(Delivery, claimed.delivery_id)
        attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'pending'
    assert delivery.lease_token is None
    assert attempt.outcome == 'unknown'
    assert "lease expired" in attempt.error_summary 
    

async def test_does_not_reap_live_lease(live_claimed_delivery):
    
    claimed = live_claimed_delivery
    
    async with session_scope() as session:
        reaped = await reap_expired_leases(session=session)
        
    assert reaped == 0
    
    async with session_scope() as session:
        delivery = await session.get(Delivery, claimed.delivery_id)
        attempt = await session.get(DeliveryAttempt, claimed.attempt_id)
        
    assert delivery.status == 'in_progress'
    assert delivery.lease_token is not None
    assert attempt.outcome is None

    
async def test_batch_size_respected(expired_claimed_delivery):
    
    claimed = expired_claimed_delivery
    endpoint_ids = []
    async with session_scope() as session:
        
        for i in range(2):
            endpoint_id = uuid.uuid4().hex
            endpoint_ids.append(endpoint_id)
            new_endpoint= Endpoint(id = endpoint_id, tenant_id = TENANT_ID, url = f'demo_url-{i}', signing_secret_ref=SECRET_REF)
            session.add(new_endpoint)
            await session.flush()
            delivery_id = uuid.uuid4().hex
            lease_token = uuid.uuid4().hex
            lease_expiry = datetime.now(timezone.utc) - timedelta(seconds=60)
            new_delivery = Delivery(id = delivery_id, event_id = claimed.event_id, endpoint_id=endpoint_id, status = 'in_progress', lease_token= lease_token, lease_expiry = lease_expiry, attempt_count = 1)
                    
            session.add(new_delivery)
            await session.flush()
                    
            attempt_id = uuid.uuid4().hex
            new_attempt = DeliveryAttempt(id = attempt_id, delivery_id = delivery_id, attempt_number = 1)
            session.add(new_attempt)
    
    try:
        
        async with session_scope() as session:
            reaped = await reap_expired_leases(session = session, batch_size=2)
        assert reaped == 2
        
        async with session_scope() as session:
            second = await reap_expired_leases(session=session, batch_size=2)
        assert second == 1 

        async with session_scope() as session:
            third = await reap_expired_leases(session=session, batch_size=2)
        assert third == 0
    finally:
        
        async with session_scope() as session:
            await session.execute(text("DELETE FROM delivery_attempts"))
            await session.execute(text("DELETE FROM deliveries"))
            for endpoint_id in endpoint_ids:
                await session.execute(text(
                    """
                        DELETE FROM endpoints
                        WHERE id = :id
                    """
            ),{"id":endpoint_id})
                
   
    
    

    
        
    